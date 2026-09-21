import unittest

from unfolding_engine.models import (
    MappingConfig,
    MappingDefinition,
    MappingTarget,
    ParsedQuery,
    SourceDefinition,
    StatementPattern,
)
from unfolding_engine.unfolder import Unfolder


class TestUnfolder(unittest.TestCase):

    def make_config(self):
        return MappingConfig(
            prefixes={
                "traffic": "http://example.org/traffic#",
            },
            sources={
                "follows": SourceDefinition(
                    source_id="follows",
                    query=(
                        "MATCH (a)-[:FOLLOWS]->(b)\n"
                        "RETURN a.id AS subject_id, "
                        "b.id AS object_id"
                    ),
                ),
            },
            mappings=[
                MappingDefinition(
                    mapping_id="M-Follows",
                    source="follows",
                    target=MappingTarget(
                        subject="traffic:vehicle_{{subject_id}}",
                        predicate="traffic:follows",
                        object="traffic:vehicle_{{object_id}}",
                    ),
                ),
            ],
        )

    def test_basic_unfolding(self):
        query = ParsedQuery(
            select_variables=["x", "y"],
            distinct=True,
            patterns=[
                StatementPattern(
                    "?x",
                    "traffic:follows",
                    "?y",
                ),
            ],
        )

        cypher = Unfolder(
            self.make_config()
        ).unfold(query)

        self.assertIn("UNWIND tp0_rows AS tp0_row", cypher)
        self.assertIn("RETURN DISTINCT", cypher)
        self.assertIn("tp0_x AS x", cypher)
        self.assertIn("tp0_y AS y", cypher)


if __name__ == "__main__":
    unittest.main()
