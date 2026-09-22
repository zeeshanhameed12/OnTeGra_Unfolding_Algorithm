from __future__ import annotations

import re

from .models import (
    IntervalTerm,
    ParsedQuery,
    StatementPattern,
)


class SparqlParser:

    # ========================================================
    # SELECT
    # ========================================================
        # select_re contains a regular expression pattern that matches the SELECT clause of a SPARQL query. It captures the DISTINCT keyword (if present) and the variables being selected. The pattern is case-insensitive and allows for multiline queries.
    SELECT_RE = re.compile(

        r"SELECT\s+"
        r"(DISTINCT\s+)?"
        r"(?P<vars>.*?)"
        r"\s+WHERE\s*\{",

        re.IGNORECASE
        |
        re.DOTALL,
    )
    # ========================================================
    # GRAPH BLOCK
    # ========================================================

    GRAPH_RE = re.compile(

        r"GRAPH\s+"
        r"(?P<graph>\?\w+)"
        r"\s*\{"
        r"(?P<body>.*?)"
        r"\}",

        re.IGNORECASE
        |
        re.DOTALL,
    )


    # ========================================================
    # SIMPLE TRIPLE
    # ========================================================

    TRIPLE_RE = re.compile(

        r"(?P<subject>\S+)"
        r"\s+"

        r"(?P<predicate>\S+)"
        r"\s+"

        r"(?P<object>\S+)"
        r"\s*\."
    )


    # ========================================================
    # PUBLIC PARSE METHOD
    # ========================================================

    def parse(
        self,
        query: str,
    ) -> ParsedQuery:

        # ----------------------------------------------------
        # SELECT
        # ----------------------------------------------------

        select_match = (
            self.SELECT_RE.search(
                query
            )
        )


        if not select_match:

            raise ValueError(
                "Could not parse SELECT clause."
            )


        distinct = bool(
            select_match.group(1)
        )


        select_variables = re.findall(

            r"\?"
            r"([A-Za-z_][A-Za-z0-9_]*)",

            select_match.group(
                "vars"
            ),
        )


        # ----------------------------------------------------
        # Parse temporal graph patterns
        # ----------------------------------------------------

        temporal_patterns = (
            self._parse_temporal_patterns(
                query
            )
        )


        if not temporal_patterns:

            raise ValueError(
                "No supported statement "
                "patterns found."
            )


        return ParsedQuery(

            select_variables=(
                select_variables
            ),

            distinct=distinct,

            patterns=temporal_patterns,
        )


    # ========================================================
    # PARSE TEMPORAL PATTERNS
    # ========================================================

    def _parse_temporal_patterns(
        self,
        query: str,
    ) -> list[StatementPattern]:

        patterns = []


        # ----------------------------------------------------
        # Find all normal triples outside/inside query.
        #
        # We use them later to discover temporal metadata.
        # ----------------------------------------------------

        all_triples = (
            self._extract_all_triples(
                query
            )
        )


        # ----------------------------------------------------
        # Process every GRAPH block.
        # ----------------------------------------------------

        for graph_match in (
            self.GRAPH_RE.finditer(
                query
            )
        ):

            graph_variable = (
                graph_match.group(
                    "graph"
                )
            )

            graph_body = (
                graph_match.group(
                    "body"
                )
            )


            graph_triples = (
                self._extract_all_triples(
                    graph_body
                )
            )


            for (
                subject,
                predicate,
                object_,
            ) in graph_triples:

                # --------------------------------------------
                # Look for interval associated
                # with this graph.
                # --------------------------------------------

                interval_variable = (
                    self._find_object(
                        all_triples,
                        graph_variable,
                        "time:hasTime",
                    )
                )


                interval = None


                if (
                    interval_variable
                    is not None
                ):

                    start = (
                        self._find_object(
                            all_triples,
                            interval_variable,
                            "traffic:start",
                        )
                    )


                    end = (
                        self._find_object(
                            all_triples,
                            interval_variable,
                            "traffic:end",
                        )
                    )


                    if (
                        start is not None
                        and
                        end is not None
                    ):

                        interval = (
                            IntervalTerm(
                                start=start,
                                end=end,
                            )
                        )


                patterns.append(

                    StatementPattern(

                        subject=subject,

                        predicate=predicate,

                        object=object_,

                        interval=interval,
                    )
                )


        return patterns


    # ========================================================
    # EXTRACT TRIPLES
    # ========================================================

    def _extract_all_triples(
        self,
        text: str,
    ) -> list[
        tuple[str, str, str]
    ]:

        triples = []


        for match in (
            self.TRIPLE_RE.finditer(
                text
            )
        ):

            triples.append(
                (
                    match.group(
                        "subject"
                    ),

                    match.group(
                        "predicate"
                    ),

                    match.group(
                        "object"
                    ),
                )
            )


        return triples


    # ========================================================
    # FIND OBJECT
    # ========================================================

    def _find_object(
        self,
        triples: list[
            tuple[str, str, str]
        ],
        subject: str,
        predicate: str,
    ) -> str | None:

        for (
            triple_subject,
            triple_predicate,
            triple_object,
        ) in triples:

            if (
                triple_subject
                ==
                subject
                and
                triple_predicate
                ==
                predicate
            ):

                return triple_object


        return None