"""Local stub for ``neo4j.exceptions``. Only the surface this codebase touches.

In the real lib, both Neo4jError (server-response errors) and DriverError (client-side / DNS / auth) share a common ``GqlError`` ancestor — that's the one to catch when you want "anything Neo4j-related went wrong."
"""

class GqlError(Exception):
    pass

class Neo4jError(GqlError):
    pass

class DriverError(GqlError):
    pass

class ServiceUnavailable(DriverError):  # noqa: N818 — name mirrors the upstream `neo4j.exceptions.ServiceUnavailable` symbol; renaming would silently break `except neo4j.exceptions.ServiceUnavailable`.
    pass

class ConfigurationError(DriverError):
    pass
