from __future__ import annotations

from .models import (
    MappingConfig,
    MappingDefinition,
    ParsedQuery,
    ResolvedPattern,
    StatementPattern,
)

from .utils import (
    mapping_term_can_produce,
)


class MappingResolver:
    """
    Determines which mappings are applicable
    to every statement pattern.

    Applicability is determined using the COMPLETE
    mapping target, not only the predicate.

    Current positions:

        subject
        predicate
        object

    Future temporal positions:

        interval_start
        interval_end
    """


    def __init__(
        self,
        config: MappingConfig,
    ):

        self.config = config


    # ========================================================
    # PUBLIC RESOLUTION METHOD
    # ========================================================

    def resolve(
        self,
        query: ParsedQuery,
    ) -> list[ResolvedPattern]:
        """
        Resolve applicable mappings for every
        statement pattern in the query.
        """

        resolved_patterns = []


        # ----------------------------------------------------
        # Process every statement pattern
        # ----------------------------------------------------

        for (
            pattern_index,
            pattern,
        ) in enumerate(
            query.patterns
        ):

            applicable_mappings = (
                self._find_applicable_mappings(
                    pattern
                )
            )


            # ------------------------------------------------
            # At least one mapping must generate the pattern
            # ------------------------------------------------

            if not applicable_mappings:

                raise ValueError(
                    "No applicable mapping found "
                    "for statement pattern: "
                    f"{pattern}"
                )


            # ------------------------------------------------
            # Store resolved result
            # ------------------------------------------------

            resolved_patterns.append(

                ResolvedPattern(

                    index=pattern_index,

                    pattern=pattern,

                    mappings=(
                        applicable_mappings
                    ),
                )
            )


        return resolved_patterns


    # ========================================================
    # FIND APPLICABLE MAPPINGS
    # ========================================================

    def _find_applicable_mappings(
        self,
        pattern: StatementPattern,
    ) -> list[MappingDefinition]:
        """
        Test all mappings against one statement pattern.
        """

        applicable = []


        for mapping in self.config.mappings:

            if self._matches(
                mapping,
                pattern,
            ):

                applicable.append(
                    mapping
                )


        return applicable


    # ========================================================
    # COMPLETE TARGET MATCHING
    # ========================================================

    def _matches(
        self,
        mapping: MappingDefinition,
        pattern: StatementPattern,
    ) -> bool:
        """
        Return True only if the complete mapping target
        can generate the query pattern.

        Example:

        Query:

            traffic:vehicle_101
            traffic:follows
            traffic:vehicle_205

        Mapping 1:

            traffic:vehicle_{{id1}}
            traffic:follows
            traffic:vehicle_{{id2}}

        -> applicable


        Mapping 2:

            traffic:person_{{id1}}
            traffic:follows
            traffic:person_{{id2}}

        -> NOT applicable
        """

        # ----------------------------------------------------
        # Query positions
        # ----------------------------------------------------

        query_terms = (
            pattern.position_terms()
        )


        # ----------------------------------------------------
        # Mapping target positions
        # ----------------------------------------------------

        target_terms = (
            mapping
            .target
            .position_terms()
        )


        # ----------------------------------------------------
        # Compare every position required by query
        # ----------------------------------------------------

        for (
            position,
            query_term,
        ) in query_terms.items():

            # ------------------------------------------------
            # Mapping cannot generate this position.
            #
            # Important for temporal queries.
            #
            # Example:
            #
            # query has interval_start
            # but mapping has no interval.
            # ------------------------------------------------

            if position not in target_terms:

                return False


            target_term = target_terms[
                position
            ]


            # ------------------------------------------------
            # Check compatibility
            # ------------------------------------------------

            compatible = (
                mapping_term_can_produce(

                    query_term=(
                        query_term
                    ),

                    target_term=(
                        target_term
                    ),

                    prefixes=(
                        self.config.prefixes
                    ),
                )
            )


            if not compatible:

                return False


        # ----------------------------------------------------
        # Every position is compatible.
        # ----------------------------------------------------

        return True