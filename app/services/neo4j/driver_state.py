"""Module-singleton mutable handle for the live Neo4j driver.

A single shared dataclass instance owns the AsyncDriver reference so the getter / closer / test fixtures can read and rewrite it without `reportPrivateUsage` warnings tripping across files.
"""

from dataclasses import dataclass

from neo4j import AsyncDriver


@dataclass
class _DriverState:
    driver: AsyncDriver | None = None


driver_state = _DriverState()
