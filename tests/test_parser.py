import unittest

from unfolding_engine.parser import SparqlParser


class TestSparqlParser(unittest.TestCase):

    def test_three_patterns(self):
        query = """
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX traffic: <http://example.org/traffic#>

        SELECT DISTINCT ?x ?y
        WHERE {
            ?x rdf:type traffic:Car .
            ?x traffic:follows ?y .
            ?y rdf:type traffic:Car .
        }
        """

        parsed = SparqlParser().parse(query)

        self.assertTrue(parsed.distinct)
        self.assertEqual(parsed.select_variables, ["x", "y"])
        self.assertEqual(len(parsed.patterns), 3)
        self.assertEqual(
            parsed.patterns[1].variable_names(),
            ["x", "y"],
        )


if __name__ == "__main__":
    unittest.main()
