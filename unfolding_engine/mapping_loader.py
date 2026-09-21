from __future__ import annotations

from pathlib import Path

import yaml

from .models import (
    MappingConfig,
    MappingDefinition,
    MappingTarget,
    SourceDefinition,
)


class MappingConfigLoader:
    """
    Loads and validates mapping.yaml.

    Responsibilities:

    1. Read YAML.
    2. Load prefixes.
    3. Load source queries.
    4. Validate mapping targets.
    5. Convert YAML dictionaries into domain objects.
    """


    def load(
        self,
        path: str | Path,
    ) -> MappingConfig:

        path = Path(
            path
        )


        # ====================================================
        # READ YAML
        # ====================================================

        with path.open(
            "r",
            encoding="utf-8",
        ) as file:

            raw = (
                yaml.safe_load(file)
                or
                {}
            )


        # ====================================================
        # PREFIXES
        # ====================================================

        prefixes = raw.get(
            "prefixes",
            {},
        )


        # ====================================================
        # SOURCES
        # ====================================================

        sources = (
            self._load_sources(
                raw.get(
                    "sources",
                    {},
                )
            )
        )


        # ====================================================
        # MAPPINGS
        # ====================================================

        mappings = (
            self._load_mappings(
                raw.get(
                    "mappings",
                    [],
                ),
                sources,
            )
        )


        # ====================================================
        # FINAL CONFIGURATION
        # ====================================================

        return MappingConfig(

            prefixes=prefixes,

            sources=sources,

            mappings=mappings,
        )


    # ========================================================
    # LOAD SOURCES
    # ========================================================

    def _load_sources(
        self,
        raw_sources: dict,
    ) -> dict[str, SourceDefinition]:

        sources = {}


        for (
            source_id,
            source_data,
        ) in raw_sources.items():

            # ------------------------------------------------
            # Validate source query
            # ------------------------------------------------

            if "query" not in source_data:

                raise ValueError(
                    f"Source '{source_id}' "
                    "does not define a query."
                )


            # ------------------------------------------------
            # Create source object
            # ------------------------------------------------

            sources[source_id] = (
                SourceDefinition(

                    source_id=source_id,

                    query=(
                        source_data[
                            "query"
                        ].strip()
                    ),
                )
            )


        return sources


    # ========================================================
    # LOAD MAPPINGS
    # ========================================================

    def _load_mappings(
        self,
        raw_mappings: list,
        sources: dict[
            str,
            SourceDefinition,
        ],
    ) -> list[MappingDefinition]:

        mappings = []

        seen_mapping_ids = set()


        for raw_mapping in raw_mappings:

            # ------------------------------------------------
            # mappingId
            # ------------------------------------------------

            if "mappingId" not in raw_mapping:

                raise ValueError(
                    "Every mapping must define "
                    "'mappingId'."
                )


            mapping_id = raw_mapping[
                "mappingId"
            ]


            # ------------------------------------------------
            # Duplicate mapping IDs
            # ------------------------------------------------

            if mapping_id in seen_mapping_ids:

                raise ValueError(
                    f"Duplicate mappingId: "
                    f"'{mapping_id}'"
                )


            seen_mapping_ids.add(
                mapping_id
            )


            # ------------------------------------------------
            # Source
            # ------------------------------------------------

            if "source" not in raw_mapping:

                raise ValueError(
                    f"Mapping '{mapping_id}' "
                    "does not define a source."
                )


            source_id = raw_mapping[
                "source"
            ]


            if source_id not in sources:

                raise ValueError(
                    f"Mapping '{mapping_id}' "
                    f"references unknown source "
                    f"'{source_id}'."
                )


            # ------------------------------------------------
            # Target
            # ------------------------------------------------

            if "target" not in raw_mapping:

                raise ValueError(
                    f"Mapping '{mapping_id}' "
                    "does not define a target."
                )


            target = raw_mapping[
                "target"
            ]


            self._validate_target(
                mapping_id,
                target,
            )


            # ------------------------------------------------
            # Interval
            # ------------------------------------------------

            interval = target.get(
                "interval"
            )


            if interval is None:

                interval = {}


            # ------------------------------------------------
            # Build MappingTarget
            # ------------------------------------------------

            mapping_target = (
                MappingTarget(

                    subject=target[
                        "subject"
                    ],

                    predicate=target[
                        "predicate"
                    ],

                    object=target[
                        "object"
                    ],

                    interval_start=(
                        interval.get(
                            "start"
                        )
                    ),

                    interval_end=(
                        interval.get(
                            "end"
                        )
                    ),
                )
            )


            # ------------------------------------------------
            # Build MappingDefinition
            # ------------------------------------------------

            mappings.append(

                MappingDefinition(

                    mapping_id=mapping_id,

                    source=source_id,

                    target=mapping_target,
                )
            )


        return mappings


    # ========================================================
    # VALIDATE COMPLETE TARGET
    # ========================================================

    def _validate_target(
        self,
        mapping_id: str,
        target: dict,
    ) -> None:
        """
        Validate that the complete target is well formed.
        """

        required_positions = [

            "subject",

            "predicate",

            "object",
        ]


        # ----------------------------------------------------
        # Validate subject/predicate/object
        # ----------------------------------------------------

        for position in required_positions:

            if position not in target:

                raise ValueError(
                    f"Mapping '{mapping_id}' "
                    f"is missing "
                    f"target.{position}"
                )


            if target[position] is None:

                raise ValueError(
                    f"Mapping '{mapping_id}' "
                    f"has empty "
                    f"target.{position}"
                )


        # ----------------------------------------------------
        # Validate temporal target
        # ----------------------------------------------------

        interval = target.get(
            "interval"
        )


        if interval is None:

            return


        if not isinstance(
            interval,
            dict,
        ):

            raise ValueError(
                f"Mapping '{mapping_id}' "
                "target.interval must be "
                "a dictionary."
            )


        has_start = (
            "start" in interval
        )


        has_end = (
            "end" in interval
        )


        # Either both start and end exist,
        # or neither should exist.

        if has_start != has_end:

            raise ValueError(
                f"Mapping '{mapping_id}' "
                "must define both "
                "target.interval.start "
                "and "
                "target.interval.end."
            )


        if has_start:

            if interval[
                "start"
            ] is None:

                raise ValueError(
                    f"Mapping '{mapping_id}' "
                    "has empty "
                    "target.interval.start."
                )


            if interval[
                "end"
            ] is None:

                raise ValueError(
                    f"Mapping '{mapping_id}' "
                    "has empty "
                    "target.interval.end."
                )