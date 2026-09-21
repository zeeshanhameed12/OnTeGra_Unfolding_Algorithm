from pathlib import Path

from unfolding_engine import (
    MappingConfigLoader,
    SparqlParser,
    Unfolder,
)


def main() -> None:
    base_dir = Path(__file__).resolve().parent

    mapping_path = base_dir / "mapping.yaml"
    query_path = base_dir / "query.sparql"
    output_path = base_dir / "unfolded.cypher"

    config = MappingConfigLoader().load(mapping_path)

    sparql_query = query_path.read_text(
        encoding="utf-8"
    )
    print("Loaded SPARQL query from:", query_path)
    parser = SparqlParser()
    parsed_query = parser.parse(sparql_query)

    print("\n==============================")
    print("SPARQL query")
    print("==============================")
    print(sparql_query)
    print("\n==============================")
    #print("Parsed SPARQL query")
    #print("==============================")
    #print("Parsed query:", parsed_query)
    


    print("SELECT variables:", parsed_query.select_variables)
    print("DISTINCT:", parsed_query.distinct)

    print("\n==============================")
    print("Statement patterns")
    print("==============================")

    for index, pattern in enumerate(parsed_query.patterns,start=1): # start=1 is used to start the enumeration from 1 instead of the default 0. This means that the first pattern will be labeled as TP1, the second as TP2, and so on.
        print(
            f"TP{index}: "
            f"{pattern.subject} "
            f"{pattern.predicate} "
            f"{pattern.object}"
        )

    unfolder = Unfolder(config)
    unfolded_cypher = unfolder.unfold(parsed_query)

    output_path.write_text(
        unfolded_cypher,
        encoding="utf-8",
    )

    print("\n==============================")
    #print("Generated unfolded Cypher")
    #print("==============================")
    #print(unfolded_cypher)

    print("\nSaved to:", output_path)


if __name__ == "__main__":
    main()
