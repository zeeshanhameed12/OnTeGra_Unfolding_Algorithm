import re

from pathlib import Path
from unfolding_engine import rdf_terms
from unfolding_engine.rdf_terms import parse_rdf_term 

base_dir = Path(__file__).resolve().parent

query_path = base_dir / "query.sparql"

sql_query = query_path.read_text(
    encoding="utf-8"
)



SELECT_RE = re.compile(

        r"SELECT\s+"
        r"(?P<distinct>DISTINCT\s+)?"
        r"(?P<variables>(?:\?\w+\s+)*)",

        re.IGNORECASE
        |
        re.DOTALL,
    )

# print("SELECT_RE pattern:", SELECT_RE.pattern)

select_match = SELECT_RE.search(sql_query)

print("SELECT match:", select_match.groupdict())

for items in select_match.groupdict():
    print(f"{items}: {select_match.group(items)}")
print

exp = rdf_terms.parse_rdf_term(
    "traffic:vehicle_{{id}}"
)

print("Parsed RDF term:", exp.kind)
print("References:", exp.references)
print("Raw:", exp.raw)

