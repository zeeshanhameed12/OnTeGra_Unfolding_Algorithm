from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import re


# ============================================================
# TERM KIND
# ============================================================

class TermKind(Enum):

    CONSTANT = "constant"

    TEMPLATE = "template"

    REFERENCE = "reference"


# ============================================================
# TEMPLATE VARIABLE REGEX
# ============================================================

_TEMPLATE_RE = re.compile(
    r"\{\{\s*"
    r"([A-Za-z_][A-Za-z0-9_]*)"
    r"\s*\}\}"
)


# ============================================================
# RDF TERM EXPRESSION
# ============================================================

@dataclass(frozen=True)
class RDFTermExpression:
    """
    Represents one mapping target term.

    Examples:

        traffic:Car
            -> CONSTANT

        traffic:vehicle_{{id}}
            -> TEMPLATE

        {{value}}
            -> REFERENCE
    """

    raw: str

    kind: TermKind

    references: tuple[str, ...] = ()


# ============================================================
# PARSE TERM
# ============================================================

def parse_rdf_term(
    value: str,
) -> RDFTermExpression:

    references = tuple(
        _TEMPLATE_RE.findall(value)
    )


    # --------------------------------------------------------
    # No placeholders
    # --------------------------------------------------------

    if not references:

        return RDFTermExpression(
            raw=value,
            kind=TermKind.CONSTANT,
        )


    # --------------------------------------------------------
    # Exactly {{column}}
    # --------------------------------------------------------

    full_reference = re.fullmatch(
        r"\{\{\s*"
        r"([A-Za-z_][A-Za-z0-9_]*)"
        r"\s*\}\}",
        value,
    )


    if full_reference:

        return RDFTermExpression(
            raw=value,
            kind=TermKind.REFERENCE,
            references=references,
        )


    # --------------------------------------------------------
    # IRI/string template
    # --------------------------------------------------------

    return RDFTermExpression(
        raw=value,
        kind=TermKind.TEMPLATE,
        references=references,
    )

class Compatibility(Enum):

    COMPATIBLE = "compatible"

    INCOMPATIBLE = "incompatible"

    POSSIBLE = "possible"