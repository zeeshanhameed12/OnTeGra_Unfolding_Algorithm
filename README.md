# Extensible SPARQL-to-Cypher Unfolding Engine

This refactor separates parsing, mapping resolution, unfolding logic, and Cypher rendering.

## Design goals

- Keep the current SPARQL triple-pattern workflow.
- Support multiple mappings for the same statement pattern using `UNION ALL`.
- Join different statement patterns using shared SPARQL variables.
- Keep `SELECT DISTINCT`.
- Introduce an extensible internal `StatementPattern` model.
- Make the model interval-ready without hard-coding interval logic throughout the engine.
- Keep Cypher-specific code out of the parser and mapping resolver.
- Make future features such as FILTER, OPTIONAL, UNION, taxonomy, and Allen interval relations easier to add.

## Project structure

```text
unfolding_engine_refactor/
├── main.py
├── mapping.yaml
├── query.sparql
├── README.md
├── unfolding_engine/
│   ├── __init__.py
│   ├── models.py
│   ├── parser.py
│   ├── mapping_loader.py
│   ├── mapping_resolver.py
│   ├── unfolder.py
│   ├── cypher_builder.py
│   └── utils.py
└── tests/
    ├── __init__.py
    ├── test_parser.py
    └── test_unfolder.py
```

## Run

```bash
pip install pyyaml
python main.py
```

The generated query is written to:

```text
unfolded.cypher
```

## Interval-ready model

Internally, a statement is represented as:

```python
StatementPattern(
    subject="?x",
    predicate="traffic:follows",
    object="?y",
    interval=None,
)
```

Later, the same engine can represent:

```python
StatementPattern(
    subject="?x",
    predicate="traffic:follows",
    object="?y",
    interval=IntervalTerm(start="?start", end="?end"),
)
```

The current parser intentionally stays compatible with ordinary SPARQL triples. Temporal query syntax should be introduced as a separate parser extension instead of embedding ad-hoc fourth-position syntax into standard SPARQL.

## Recommended next extension

Add a temporal algebra node, for example:

```python
TemporalRelation(
    relation="during",
    left_interval="p2",
    right_interval="p1",
)
```

and let `CypherBuilder` translate it into backend-specific interval conditions.
