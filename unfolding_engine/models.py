from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


# ============================================================
# INTERVAL
# ============================================================

@dataclass(frozen=True)
class IntervalTerm:
    """
    Represents the temporal interval attached to a statement.

    Example:
        start = "?P1_start"
        end   = "?P1_end"
    """

    start: str
    end: str


    def terms(self) -> list[str]:
        """
        Return all terms belonging to the interval.
        """

        return [
            self.start,
            self.end,
        ]


# ============================================================
# STATEMENT PATTERN
# ============================================================

@dataclass(frozen=True)
class StatementPattern:
    """
    Internal representation of a query statement.

    Normal RDF statement:

        subject predicate object

    Temporal statement:

        subject predicate object interval
    """

    subject: str
    predicate: str
    object: str

    interval: Optional[IntervalTerm] = None


    def terms(self) -> list[str]:
        """
        Return all terms appearing in the statement.

        Example:

        ?x traffic:follows ?y

        returns:

        [
            "?x",
            "traffic:follows",
            "?y"
        ]

        If an interval exists, its start and end
        are also included.
        """

        result = [
            self.subject,
            self.predicate,
            self.object,
        ]


        if self.interval is not None:

            result.extend(
                self.interval.terms()
            )


        return result


    def position_terms(self) -> dict[str, str]:
        """
        Return terms indexed by their semantic position.

        Normal statement:

        {
            "subject": "?x",
            "predicate": "traffic:follows",
            "object": "?y"
        }

        Temporal statement:

        {
            "subject": "?x",
            "predicate": "traffic:follows",
            "object": "?y",
            "interval_start": "?start",
            "interval_end": "?end"
        }
        """

        result = {

            "subject":
                self.subject,

            "predicate":
                self.predicate,

            "object":
                self.object,
        }


        if self.interval is not None:

            result["interval_start"] = (
                self.interval.start
            )

            result["interval_end"] = (
                self.interval.end
            )


        return result


    def variable_names(self) -> list[str]:
        """
        Return all SPARQL variables occurring in the statement.

        Example:

        ?x traffic:follows ?y

        returns:

        ["x", "y"]
        """

        variables = []


        for term in self.terms():

            if term.startswith("?"):

                variable = term[1:]


                if variable not in variables:

                    variables.append(
                        variable
                    )


        return variables


# ============================================================
# PARSED QUERY
# ============================================================

@dataclass(frozen=True)
class ParsedQuery:
    """
    Result produced by the SPARQL parser.
    """

    select_variables: list[str]

    distinct: bool

    patterns: list[StatementPattern]


# ============================================================
# MAPPING TARGET
# ============================================================

@dataclass(frozen=True)
class MappingTarget:
    """
    Complete target produced by one mapping.

    Example:

        subject:
            traffic:vehicle_{{subject_id}}

        predicate:
            traffic:follows

        object:
            traffic:vehicle_{{object_id}}

        interval:
            start: {{P1_start}}
            end: {{P1_end}}
    """

    subject: str

    predicate: str

    object: str

    interval_start: Optional[str] = None

    interval_end: Optional[str] = None


    def position_terms(self) -> dict[str, str]:
        """
        Return the complete mapping target indexed
        by semantic position.
        """

        result = {

            "subject":
                self.subject,

            "predicate":
                self.predicate,

            "object":
                self.object,
        }


        if self.interval_start is not None:

            result["interval_start"] = (
                self.interval_start
            )


        if self.interval_end is not None:

            result["interval_end"] = (
                self.interval_end
            )


        return result


# ============================================================
# MAPPING DEFINITION
# ============================================================

@dataclass(frozen=True)
class MappingDefinition:
    """
    Complete mapping definition.
    """

    mapping_id: str

    source: str

    target: MappingTarget


# ============================================================
# SOURCE
# ============================================================

@dataclass(frozen=True)
class SourceDefinition:
    """
    Defines one source query.
    """

    source_id: str

    query: str


# ============================================================
# RESOLVED PATTERN
# ============================================================

@dataclass(frozen=True)
class ResolvedPattern:
    """
    A statement pattern together with all mappings
    that can generate it.
    """

    index: int

    pattern: StatementPattern

    mappings: list[MappingDefinition]


# ============================================================
# COMPLETE MAPPING CONFIGURATION
# ============================================================

@dataclass
class MappingConfig:
    """
    Complete mapping configuration loaded from mapping.yaml.
    """

    prefixes: dict[str, str] = field(
        default_factory=dict
    )

    sources: dict[
        str,
        SourceDefinition
    ] = field(
        default_factory=dict
    )

    mappings: list[
        MappingDefinition
    ] = field(
        default_factory=list
    )