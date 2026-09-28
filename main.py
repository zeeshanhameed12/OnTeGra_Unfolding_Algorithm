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
    parsed_query = SparqlParser().parse(sparql_query)

    print("\n==============================")
    print("SPARQL query")
    print("==============================")
    print(sparql_query)
    #print("\n==============================")
    #print("Parsed SPARQL query")
    #print("==============================")
   
    


    print("SELECT variables:", parsed_query.select_variables)
    print("DISTINCT:", parsed_query.distinct)

    print("\n==============================")
    print("Statement patterns")
    print("==============================")

    i =1
    for pattern in parsed_query.patterns: 
          print(
              f"TP{i}: "
              f"{pattern.subject} "
              f"{pattern.predicate} "
              f"{pattern.object}"
          )
          i += 1

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
