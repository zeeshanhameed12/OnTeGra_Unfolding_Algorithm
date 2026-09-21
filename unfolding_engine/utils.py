from __future__ import annotations

import re


# ============================================================
# VARIABLE UTILITIES
# ============================================================

def is_variable(
    term: str,
) -> bool:
    """
    Return True if the term is a SPARQL variable.

    Example:

        ?x     -> True
        :Car   -> False
    """

    return (
        isinstance(term, str)
        and
        term.startswith("?")
    )


def variable_name(
    term: str,
) -> str:
    """
    Convert:

        ?x

    into:

        x
    """

    if not is_variable(term):

        raise ValueError(
            f"Not a SPARQL variable: {term}"
        )


    return term[1:]


# ============================================================
# SAFE NAMES
# ============================================================

def safe_name(
    value: str,
) -> str:

    return re.sub(
        r"[^A-Za-z0-9_]",
        "_",
        value,
    )


def make_alias(
    pattern_index: int,
    variable: str,
) -> str:
    """
    Example:

        pattern_index = 1
        variable = x

    becomes:

        tp1_x
    """

    return (
        f"tp{pattern_index}_"
        f"{safe_name(variable)}"
    )


# ============================================================
# PREFIX HANDLING
# ============================================================

def expand_prefixed_name(
    value: str,
    prefixes: dict[str, str],
) -> str:
    
    """
    Expand ex:term to its full IRI if the prefix is known.     
    Variables and already-full IRIs are returned unchanged.
    
    Expand:

        traffic:Car

    into:

        http://example.org/traffic#Car

    when the traffic prefix is defined.
    """

    if is_variable(value):

        return value


    if (
        value.startswith("<")
        and
        value.endswith(">")
    ):

        return value[1:-1]


    if ":" not in value:

        return value


    prefix, local = value.split(
        ":",
        1,
    )


    if prefix in prefixes:

        return (
            prefixes[prefix]
            +
            local
        )


    return value


# ============================================================
# TEMPLATE REGULAR EXPRESSION
# ============================================================

_TEMPLATE_RE = re.compile(
    r"\{\{\s*"
    r"([A-Za-z_][A-Za-z0-9_]*)"
    r"\s*\}\}"
)


# ============================================================
# NORMALIZE CONSTANT
# ============================================================

def normalize_constant(
    term: str,
    prefixes: dict[str, str],
) -> str:
    """
    Normalize query/mapping constants before comparison.

    Example:

        traffic:follows

    becomes:

        http://example.org/traffic#follows
    """

    if (
        term.startswith("<")
        and
        term.endswith(">")
    ):

        return term[1:-1]


    return expand_prefixed_name(
        term,
        prefixes,
    )


# ============================================================
# TEMPLATE COMPATIBILITY
# ============================================================

def template_can_generate(
    template: str,
    value: str,
) -> bool:
    """
    Determine whether a concrete RDF term can be generated
    by a mapping template.

    Example:

        template:
            http://example.org/traffic#vehicle_{{id}}

        value:
            http://example.org/traffic#vehicle_101

        -> True


        template:
            http://example.org/traffic#person_{{id}}

        value:
            http://example.org/traffic#vehicle_101

        -> False
    """

    regex_parts = []

    cursor = 0

    seen_variables = set()


    for match in _TEMPLATE_RE.finditer(
        template
    ):

        # ----------------------------------------------------
        # Constant text before {{variable}}
        # ----------------------------------------------------

        constant_part = template[
            cursor:match.start()
        ]


        regex_parts.append(
            re.escape(
                constant_part
            )
        )


        # ----------------------------------------------------
        # Template variable
        # ----------------------------------------------------

        variable = match.group(1)


        if variable not in seen_variables:

            regex_parts.append(
                rf"(?P<{variable}>.+?)"
            )

            seen_variables.add(
                variable
            )


        else:

            # Same variable occurs again.
            #
            # Example:
            #
            # person_{{id}}_friend_{{id}}
            #
            # Both values must be identical.

            regex_parts.append(
                rf"(?P={variable})"
            )


        cursor = match.end()


    # --------------------------------------------------------
    # Remaining constant part
    # --------------------------------------------------------

    remaining = template[cursor:]


    regex_parts.append(
        re.escape(
            remaining
        )
    )


    # --------------------------------------------------------
    # Full regular expression
    # --------------------------------------------------------

    regex = "".join(
        regex_parts
    )


    return (
        re.fullmatch(
            regex,
            value,
        )
        is not None
    )


# ============================================================
# COMPLETE TERM COMPATIBILITY
# ============================================================

def mapping_term_can_produce(
    query_term: str,
    target_term: str,
    prefixes: dict[str, str],
) -> bool:
    """
    Check whether one mapping-target term can produce
    the corresponding query term.

    Rules:

    1. Query variable:
           compatible with any target term.

    2. Query constant + target constant:
           constants must be equal.

    3. Query constant + target template:
           template must be capable of generating
           the query constant.
    """

    # --------------------------------------------------------
    # Rule 1:
    # Query variable places no constant restriction.
    # --------------------------------------------------------

    if is_variable(
        query_term
    ):

        return True


    # --------------------------------------------------------
    # Normalize both sides
    # --------------------------------------------------------

    query_value = normalize_constant(
        query_term,
        prefixes,
    )


    target_value = normalize_constant(
        target_term,
        prefixes,
    )


    # --------------------------------------------------------
    # Rule 2/3:
    # Mapping target is a template.
    # --------------------------------------------------------

    if _TEMPLATE_RE.search(
        target_value
    ):

        return template_can_generate(
            target_value,
            query_value,
        )


    # --------------------------------------------------------
    # Constant-to-constant comparison
    # --------------------------------------------------------

    return (
        query_value
        ==
        target_value
    )


# ============================================================
# TEMPLATE TO CYPHER
# ============================================================

def template_to_cypher(
    template: str,
    prefixes: dict[str, str],
) -> str:
    """
    Convert a mapping template into a Cypher expression.

    Example:

        traffic:vehicle_{{id}}

    becomes approximately:

        'http://example.org/traffic#vehicle_'
        + toString(id)
    """

    expanded = template


    # --------------------------------------------------------
    # Expand prefix
    # --------------------------------------------------------

    if (
        ":" in expanded
        and
        not expanded.startswith(
            (
                "http://",
                "https://",
            )
        )
    ):

        prefix, rest = expanded.split(
            ":",
            1,
        )


        if prefix in prefixes:

            expanded = (
                prefixes[prefix]
                +
                rest
            )


    # --------------------------------------------------------
    # Find template variables
    # --------------------------------------------------------

    matches = list(
        _TEMPLATE_RE.finditer(
            expanded
        )
    )


    # Constant target
    if not matches:

        return repr(
            expanded
        )


    parts = []

    cursor = 0


    for match in matches:

        constant_part = expanded[
            cursor:match.start()
        ]


        if constant_part:

            parts.append(
                repr(
                    constant_part
                )
            )


        variable = match.group(1)


        parts.append(
            f"toString({variable})"
        )


        cursor = match.end()


    # --------------------------------------------------------
    # Remaining constant part
    # --------------------------------------------------------

    remaining = expanded[cursor:]


    if remaining:

        parts.append(
            repr(
                remaining
            )
        )


    return " + ".join(
        parts
    )