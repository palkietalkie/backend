"""Type alias for the asyncpg connection types we accept everywhere.

A direct asyncpg ``Connection`` and a pooled ``PoolConnectionProxy`` are duck-typed at runtime (proxy forwards every Connection method via ``__getattr__``), but the asyncpg stubs don't expose that relationship. Routers and helpers accept either via this alias."""

import asyncpg
from asyncpg.pool import PoolConnectionProxy

type DBConn = asyncpg.Connection | PoolConnectionProxy
