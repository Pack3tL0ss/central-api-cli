from centralcli import config, render

from .migrate import migrate_all

if not config.cache.ok and config.tinydb_cache.ok:  # pragma: no cover
    render.econsole.print(":tada: :zap: :zap: A new faster cache database has been implemented.  Migrating current Cache")
    migrate_all()
    config.cache.ok = True  # prevents check_fresh from auto refreshing after migration

from .sqlite import Cache, DBAction

__all__ = [
    Cache,
    DBAction
]
