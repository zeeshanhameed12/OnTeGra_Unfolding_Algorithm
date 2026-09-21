from __future__ import annotations

from .models import (
    MappingConfig,
    MappingDefinition,
    ResolvedPattern,
)
from .utils import (
    is_variable,
    make_alias,
    template_to_cypher,
    variable_name,
)


class CypherBuilder:
    """
    Backend-specific Cypher generation.

    The rest of the unfolding engine does not need to know the concrete Cypher
    syntax used here.
    """

    def __init__(self, config: MappingConfig):
        self.config = config

    def build_pattern_relation(
        self,
        resolved: ResolvedPattern,
    ) -> str:
        pattern = resolved.pattern
        tp_index = resolved.index
        variables = pattern.variable_names()

        if not variables:
            raise ValueError(
                "Current implementation expects at least one variable "
                "in every statement pattern."
            )

        aliases = [
            make_alias(tp_index, variable)
            for variable in variables
        ]

        branches = [
            self._build_mapping_branch(tp_index, pattern, mapping)
            for mapping in resolved.mappings
        ]

        union_body = "\nUNION ALL\n".join(branches)

        row_fields = ", ".join(
            f"{alias}: {alias}"
            for alias in aliases
        )

        row_map = "{" + row_fields + "}"

        return f"""
CALL () {{
    CALL () {{
{self._indent(union_body, 8)}
    }}

    WITH {", ".join(aliases)}

    RETURN collect(
        DISTINCT {row_map}
    ) AS tp{tp_index}_rows
}}
""".strip()

    def _build_mapping_branch(
        self,
        tp_index: int,
        pattern,
        mapping: MappingDefinition,
    ) -> str:
        if mapping.source not in self.config.sources:
            raise ValueError(
                f"Mapping '{mapping.mapping_id}' refers to unknown "
                f"source '{mapping.source}'."
            )

        source_query = self.config.sources[mapping.source].query

        subject_expr = template_to_cypher(
            mapping.target.subject,
            self.config.prefixes,
        )
        predicate_expr = template_to_cypher(
            mapping.target.predicate,
            self.config.prefixes,
        )
        object_expr = template_to_cypher(
            mapping.target.object,
            self.config.prefixes,
        )

        return_expressions: list[str] = []

        if is_variable(pattern.subject):
            variable = variable_name(pattern.subject)
            return_expressions.append(
                f"{subject_expr} AS {make_alias(tp_index, variable)}"
            )

        if is_variable(pattern.predicate):
            variable = variable_name(pattern.predicate)
            return_expressions.append(
                f"{predicate_expr} AS {make_alias(tp_index, variable)}"
            )

        if is_variable(pattern.object):
            variable = variable_name(pattern.object)
            return_expressions.append(
                f"{object_expr} AS {make_alias(tp_index, variable)}"
            )

        # Interval support is intentionally located here rather than spread
        # through the whole program.
        if pattern.interval is not None:
            if mapping.target.interval_start is None:
                raise ValueError(
                    f"Mapping '{mapping.mapping_id}' has no interval.start."
                )
            if mapping.target.interval_end is None:
                raise ValueError(
                    f"Mapping '{mapping.mapping_id}' has no interval.end."
                )

            start_expr = template_to_cypher(
                mapping.target.interval_start,
                self.config.prefixes,
            )
            end_expr = template_to_cypher(
                mapping.target.interval_end,
                self.config.prefixes,
            )

            if is_variable(pattern.interval.start):
                variable = variable_name(pattern.interval.start)
                return_expressions.append(
                    f"{start_expr} AS {make_alias(tp_index, variable)}"
                )

            if is_variable(pattern.interval.end):
                variable = variable_name(pattern.interval.end)
                return_expressions.append(
                    f"{end_expr} AS {make_alias(tp_index, variable)}"
                )

        if not return_expressions:
            raise ValueError(
                "Pattern branch produced no variables to return."
            )

        return f"""
CALL () {{
{self._indent(source_query, 4)}
}}
RETURN DISTINCT
    {", ".join(return_expressions)}
""".strip()

    @staticmethod
    def _indent(text: str, spaces: int) -> str:
        prefix = " " * spaces
        return "\n".join(
            prefix + line if line.strip() else line
            for line in text.splitlines()
        )
