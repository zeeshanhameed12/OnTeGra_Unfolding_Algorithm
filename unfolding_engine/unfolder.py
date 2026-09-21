from __future__ import annotations

from .cypher_builder import CypherBuilder # . indicates that the CypherBuilder class is being imported from the cypher_builder module within the same package as the current module. This allows the Unfolder class to use the functionality provided by the CypherBuilder class for constructing Cypher queries.
from .mapping_resolver import MappingResolver
from .models import MappingConfig, ParsedQuery
from .utils import make_alias


class Unfolder:
    """
    Main application service.

    Responsibilities:
    - resolve mappings,
    - ask the backend builder for one relation per statement pattern,
    - build joins from shared variables,
    - build final projection.

    It deliberately does not parse files and does not load YAML itself.
    """

    def __init__(self, config: MappingConfig): # def __init__(self, config: MappingConfig): is the constructor method for the Unfolder class. It takes a single argument, config, which is expected to be an instance of the MappingConfig class. This method initializes the Unfolder instance by setting up its configuration and creating instances of MappingResolver and CypherBuilder, which are used for resolving mappings and building Cypher queries, respectively.
        self.config = config # config is an instance of the MappingConfig class that contains the configuration settings for the Unfolder. It is stored as an instance variable self.config so that it can be accessed by other methods within the Unfolder class.
        self.resolver = MappingResolver(config)
        self.cypher_builder = CypherBuilder(config)

    def unfold(self, query: ParsedQuery) -> str:
        resolved_patterns = self.resolver.resolve(query)

        parts: list[str] = []

        # 1. Materialize one relation for each statement pattern.
        for resolved in resolved_patterns:
            parts.append(self.cypher_builder.build_pattern_relation(resolved))

        # 2. Join statement-pattern relations using shared variables.
        bound: dict[str, str] = {}

        for index, pattern in enumerate(query.patterns):
            variables = pattern.variable_names()

            row_name = f"tp{index}_row"
            rows_name = f"tp{index}_rows"

            join_conditions: list[str] = []

            for variable in variables:
                if variable in bound:
                    current_alias = make_alias(index, variable)
                    previous_alias = bound[variable]

                    join_conditions.append(
                        f"{row_name}.{current_alias} = {previous_alias}"
                    )

            rows_to_unwind = rows_name

            if join_conditions:
                condition = " AND ".join(join_conditions)
                rows_to_unwind = (
                    f"[{row_name} IN {rows_name} "
                    f"WHERE {condition}]"
                )

            parts.append(
                f"UNWIND {rows_to_unwind} AS {row_name}"
            )

            aliases = [
                make_alias(index, variable)
                for variable in variables
            ]

            assignments = [
                f"{row_name}.{alias} AS {alias}"
                for alias in aliases
            ]

            parts.append(
                "WITH *, " + ", ".join(assignments)
            )

            for variable, alias in zip(variables, aliases):
                bound.setdefault(variable, alias)

        # 3. Final projection.
        projection: list[str] = []

        for variable in query.select_variables:
            if variable not in bound:
                raise ValueError(
                    f"SELECT variable ?{variable} does not occur "
                    "in supported statement patterns."
                )

            projection.append(
                f"{bound[variable]} AS {variable}"
            )

        distinct_keyword = "DISTINCT " if query.distinct else ""

        parts.append(
            "RETURN "
            + distinct_keyword
            + "\n    "
            + ",\n    ".join(projection)
        )

        return "\n\n".join(parts)
