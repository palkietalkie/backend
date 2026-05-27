"""Local stub for ``neo4j.exceptions``. Only the surface this codebase touches."""

class Neo4jError(Exception):
    pass

class ServiceUnavailable(Neo4jError):
    pass
