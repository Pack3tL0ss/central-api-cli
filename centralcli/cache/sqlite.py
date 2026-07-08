import asyncio
import datetime as dt
import time
from collections.abc import Generator, Iterable, Iterator, Sequence
from copy import deepcopy
from enum import Enum
from functools import cached_property, wraps
from importlib.util import find_spec
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Literal, Optional, overload

import pendulum
import typer
from pydantic import ValidationError
from rich.console import Console
from rich.markup import escape
from sqlalchemy import Engine, MetaData, String, and_, cast, create_engine, delete, func, insert, or_, select, update
from sqlalchemy.orm import Session

from centralcli import api_clients, config, constants, log, render, utils
from centralcli.client import BatchRequest
from centralcli.client import Session as ClientSession
from centralcli.cnx.models import cache as cnx_models
from centralcli.cnx.models.cache import get_inventory_with_sub_data
from centralcli.environment import env
from centralcli.models import cache as models
from centralcli.models.sql import (
    MPSK,
    Base,
    Building,
    CacheTable,
    CentralAuditLog,
    Cert,
    Client,
    Device,
    Event,
    FloorPlanAP,
    GLPService,
    Group,
    Guest,
    InventoryDevice,
    Label,
    MPSKNetwork,
    Portal,
    Site,
    Subscription,
    SubscriptionName,
    Template,
    WebHookData,
)
from centralcli.objects import DateTime
from centralcli.objects.cache import (
    CacheAuditLog,
    CacheBuilding,
    CacheCert,
    CacheClient,
    CacheDevice,
    CacheEvent,
    CacheFloorPlanAP,
    CacheGroup,
    CacheGuest,
    CacheInvDevice,
    CacheInvMonDevice,
    CacheLabel,
    CacheMpsk,
    CacheMpskNetwork,
    CacheObject,
    CachePortal,
    CacheResponses,
    CacheService,
    CacheSite,
    CacheSub,
    CacheTemplate,
    CentralObject,
    MigrateDevice,
)
from centralcli.response import BatchResponse, CombinedResponse, Response
from centralcli.strings import emoji
from centralcli.typedefs import typed_lru_cache

if TYPE_CHECKING:

    from centralcli.config import Config
    from centralcli.typedefs import MPSKStatus, SiteData


if find_spec("fuzzywuzzy"):
    from fuzzywuzzy import process
    FUZZ = True
else:
    FUZZ = False


class DBAction(str, Enum):
    INSERT = "INSERT"
    UPDATE = "UPDATE"
    UPSERT = "UPSERT"
    DELETE = "DELETE"
    REPLACE = "REPLACE"


_SPIN_EMOJI_MAP = {
    "INSERT": ":heavy_plus_sign:",
    "UPDATE": ":floppy_disk:",
    "UPSERT": ":floppy_disk:",
    "DELETE": ":wastebasket:",
    "REPLACE": ":heavy_plus_sign:",
}

api = api_clients.classic
# Used to debug completion
econsole = Console(stderr=True)
console = Console()


def ensure_config(function):
    """Prevents exception during completion when config missing or invalid."""
    @wraps(function)
    def wrapper(*args, **kwargs):
        if not config.valid:
            econsole.print(":warning:  Invalid or missing config", end="")
            return []
        return function(*args, **kwargs)

    return wrapper


def _handle_multi_word_incomplete(incomplete: str) -> tuple[str, str]:
    if incomplete.startswith("'"):
        pfx = "'"
    elif incomplete.startswith('"'):
        pfx = '"'
    else:
        pfx = ""
    if pfx:
        incomplete = incomplete.lstrip(pfx)

    return incomplete, pfx


class TableInfo:
    def __init__(self, name: str, table: CacheTable, records: int, engine: Engine):
        self.name = name
        self.records = records
        self._table = table
        self._engine = engine

    def all(self):
        with self._engine.connect() as connection:
            start = time.perf_counter()
            result = connection.execute(select(self._table))
            end = time.perf_counter() - start
            log.debug(f"All ({self.records}) {self.name} fetched via TableInfo.all()  in {round(end - start, 3)}")
            return [dict(row) for row in result.mappings()]

    def __len__(self):
        return self.records


class Cache:
    config: Config = None

    @classmethod
    def set_config(cls, config: Config) -> None:
        cls.config = config

    def __init__(
        self,
        config: Config,
    ) -> None:
        """Central-API-CLI Cache object
        """
        self.init(config)

    def init(self, config: Config) -> None:
        self.config = config
        self.engine = self.create_engine()
        self.responses = CacheResponses()
        if config.valid and config.cache_dir.exists():
            self._tables: list[CacheTable] = [Device, InventoryDevice, Site, Group, Template, Label, Client, SubscriptionName]
            if config.glp.ok:
                self._tables += [Subscription, GLPService]

    def __call__(self, refresh=False) -> list[Response]:
        if refresh:
            return self.check_fresh(refresh=refresh)

    def __iter__(self) -> Iterator[tuple[str, list[Base]]]:
        yield from self.all_tables

    def __len__(self) -> int:
        return len(list(self.all_tables))

    def __repr__(self) -> str:  # pragma: no cover  used for debug
        return f"<{self.__module__}.{type(self).__name__} ({self.config.workspace}) object at {hex(id(self))}>"

    def is_central_license(self, license: str) -> bool:
        if not any(
            [
                license.startswith("enhanced_"),
                license.startswith("standard_"),
                license.endswith("hciaas"),
                license.endswith("baas"),
                "_vm_" in license,
                license.endswith("zerto"),
                license in {"sta", "stb", "stc", "bridge", "st", "pr", "es", "et", "special"},
                license.startswith("private_cloud"),
                "k8s" in license,
                "proliant" in license,
                license.endswith("_storage"),
                license.endswith("edgeline"),
                license.endswith("hci_manager"),
                license.endswith("_sfm"),
                "alletra" in license,
                "_sensor_" in license
            ]
        ):
            return True
        else:
            return False

    async def _execute_statements(self, statements: list, action: DBAction, table_name: str, record_cnt: int) -> int:
        with Session(self.engine) as session:
            start = time.perf_counter()
            results = [session.execute(stmt) for stmt in statements]
            updated_count = sum([r.rowcount for r in results])
            session.commit()
            no_change_msg = '' if record_cnt == updated_count else f"({record_cnt - updated_count} records did not change, no match to query) "
            workspace_msg = '' if self.config.workspace == self.config.default_workspace else f"({self.config.workspace} workspace) "
            log.info(f"{action.value} {record_cnt} items in {table_name} table {workspace_msg}{no_change_msg}in {round(time.perf_counter() - start, 3)}s")

            return updated_count

    def create_engine(self) -> Engine:
        engine = create_engine(f"sqlite:///{str(self.config.cache.file)}")
        Base.metadata.create_all(engine)
        return engine

    def _get_all(self, table: CacheTable, obj: CacheObject | Callable | None = None) -> Generator[CacheObject | CacheTable, None, None]:
        with Session(self.engine) as session:
            start = time.perf_counter()
            matches: list[CacheTable] = session.scalars(select(table)).all()
            log.debug(f"All ({len(matches)}) {table.__name__} fetched via Cache._get_all in {round(time.perf_counter() - start, 3)}s")
            if obj:
                kwargs = {} if obj not in [CacheGuest, CacheFloorPlanAP] else {"cache": self}
                if obj is not CacheCert:
                    yield from (obj(m.to_dict(), **kwargs) for m in matches)
                else:
                    yield from (obj(**m.to_dict(), **kwargs) for m in matches)
            else:
                yield from (m for m in matches)

    async def _update_db(self, table: CacheTable, data: list[dict[str, Any]], action: DBAction = DBAction.UPSERT, column: str | tuple = None) -> bool:
        data = utils.listify(data)
        try:
            with render.Spinner(f"{_SPIN_EMOJI_MAP[action.value]}  [medium_spring_green]{table.__tablename__}[/] cache {action.value} {len(data)} records"):
                if action == DBAction.DELETE:
                    if isinstance(column, str):
                        statements = [delete(table).where(getattr(table, column) == item[column]) for item in data]  # TODO list comp w/ compound where clause using or_
                    else:  # hard coded at 2 cols for templates right now
                        statements = [delete(table).where(and_(getattr(table, column[0]) == item[column[0]], getattr(table, column[1]) == item[column[1]])) for item in data]
                elif action == DBAction.UPDATE:
                    statements = [update(table).where(getattr(table, column) == item[column]).values(**item) for item in data]
                elif action == DBAction.UPSERT:
                    with Session(self.engine) as session:
                        start = time.perf_counter()
                        results = [session.merge(table(**item)) for item in data]  # This returns a list of the Table objects (that matched the where clause)
                        session.commit()
                        workspace_msg = '' if self.config.workspace == self.config.default_workspace else f"({self.config.workspace} workspace) "
                        log.info(f"{action.value} {len(results)} items in {table.__tablename__} table {workspace_msg}in {round(time.perf_counter() - start, 3)}s")
                        return len(results) == len(data)
                else:  # INSERT/REPLACE (truncate then insert)
                    if action == DBAction.REPLACE:
                        with self.engine.connect() as connection:
                            connection.execute(delete(table))
                            connection.commit()
                    statements = [insert(table).values(chunk) for chunk in utils.chunker(data, 999)]  # sqlite can process 999 entries at a time beyond that will throw "too many variables"

                updated_rows = await self._execute_statements(statements, action=action, table_name=table.__tablename__, record_cnt=len(data))
                return updated_rows == len(data)
        except Exception as e:
            log.exception(f"{repr(e)} occured during attempt to {action.value} {len(data)} records from {table.__tablename__} cache (Cache._update_db)", caption=True, log=True)
            if "UNIQUE constraint failed: devices.serial" in repr(e):
                dump_file = config.log_dir / "sql_dump_data.json"
                import json
                dump_file.write_text(json.dumps(data, indent=4))
                log.error(f"Data that caused the sqlite3.IntegrityError exception written to {dump_file}", show=True, caption=True, log=True)
            if env.is_pytest:
                raise e

    async def _delete_from_db(self, table: CacheTable, data: list[dict[str, Any]], column: str):
        statements = [delete(table).where(getattr(table, column) == dev[column]) for dev in data]  # TODO list comp w/ compound where clause using or_
        with Session(self.engine) as session:
            start = time.perf_counter()
            [session.execute(statement) for statement in statements]
            session.commit()
            log.debug(f"Removed ({len(data)}) devices from {table.__name__} table in {round(time.perf_counter() - start, 3)}")

    @property
    def size(self) -> str:
        def human_size(size_in_bytes: int | float, suffix: str = "B") -> str:
            for unit in ("", "K", "M", "G", "T", "P", "E", "Z"):
                if abs(size_in_bytes) < 1024.0:
                    return f"{size_in_bytes:3.1f}{unit}{suffix}"
                size_in_bytes /= 1024.0
            return f"{size_in_bytes:.1f}Y{suffix}"

        if self.config is not None:
            db_stats = self.config.cache.file.stat()
            return human_size(db_stats.st_size)

        return "0"

    @property
    def all_tables(self) -> Generator[TableInfo, None, None]:
        metadata = MetaData()
        metadata.reflect(bind=self.engine)
        tables = []
        with Session(self.engine) as session:
            for table_name, table in metadata.tables.items():
                count_stmt = select(func.count()).select_from(table)
                row_count = session.scalar(count_stmt)
                tables += [TableInfo(table_name, table, row_count, engine=self.engine)]

        for t in tables:
            yield t

    @property
    def key_tables(self) -> Generator[TableInfo, None, None]:
        _key_tables = [t.__tablename__ for t in self._tables]
        _tables = [t for t in self.all_tables if t.name in _key_tables]
        for table in _tables:
            yield table

    @property
    def devices(self) -> Generator[CacheDevice, None, None]:
        yield from self._get_all(Device, CacheDevice)

    @property
    def inv_device_types(self) -> set[str]:
        return set() if not self.inventory else set(d.type for d in self.inventory)

    @property
    def mon_device_types(self) -> set[str]:
        return set(d.type for d in self.devices)

    @property
    def devices_by_serial(self) -> dict[str, CacheDevice]:
        return {d.serial: d for d in self.devices}

    @property
    def inventory(self) -> Generator[CacheInvDevice, None, None]:
        yield from self._get_all(InventoryDevice, CacheInvDevice)

    @property
    def inventory_by_serial(self) -> dict[str, list[dict[str, Any]]]:
        return {d.serial: dict(d) for d in self.inventory}

    @property
    def inventory_by_id(self) -> dict[str, list[dict[str, Any]]]:
        return {d.id: dict(d) for d in self.inventory}

    @property
    def subscriptions(self) -> Generator[CacheSub, None, None]:
        subs = list(self._get_all(Subscription, CacheSub))
        for sub in sorted(subs, key=lambda s: (s.expired, s.name)):
            yield sub

    @property
    def subscriptions_by_id(self) -> dict[str, list[dict[str, Any]]]:
        return {s.id: dict(s) for s in self.subscriptions}

    @property
    def subscriptions_by_key(self) -> dict[str, list[dict[str, Any]]]:
        return {s.key: dict(s) for s in self.subscriptions}

    @property
    def sites(self) -> Generator[CacheSite, None, None]:
        yield from self._get_all(Site, CacheSite)

    @property
    def sites_by_id(self) -> dict[str, list[dict[str, Any]]]:
        return {s.id: dict(s) for s in self.sites}

    @property
    def sites_by_name(self) -> dict[str, list[dict[str, Any]]]:
        return {s.name: dict(s) for s in self.sites}

    @property
    def groups(self) -> Generator[CacheGroup, None, None]:
        yield from self._get_all(Group, CacheGroup)

    @property
    def groups_by_name(self) -> dict[str, list[dict[str, Any]]]:
        return {g.name: dict(g) for g in self.groups}

    @property
    def group_names(self) -> list[str]:
        return [g.name for g in self.groups]

    @property
    def ap_groups(self) -> list[CacheGroup]:
        return [g for g in self.groups if "ap" in g.allowed_types and g.name]

    @property
    def ap_ui_groups(self) -> list[CacheGroup]:
        return [g for g in self.ap_groups if not g.wlan_tg]

    @property
    def labels(self) -> Generator[CacheLabel, None, None]:
        yield from self._get_all(Label, CacheLabel)

    @property
    def labels_by_name(self) -> dict[str, CacheLabel]:
        return {label.name: label for label in self.labels}

    @property
    def label_names(self) -> list[str]:
        return [label.name for label in self.labels]

    @property
    def services(self) -> Generator[CacheService, None, None]:
        svc = self._get_all(GLPService, CacheService)
        if not svc:  # pragma: no cover
            asyncio.run(self.refresh_svc_db())
            svc = self._get_all(GLPService, CacheService)

        yield from svc

    @property
    def services_by_name(self) -> dict[str, CacheService]:
        return {svc.name: svc for svc in self.services}

    @property
    def my_service(self) -> CacheService:
        key = "public" if self.config.cluster != "internal" else "internal"
        return self.services_by_name[key]

    @cached_property
    def licenses(self) -> list[str]:
        sub_names = [sub.name for sub in self._get_all(SubscriptionName)]
        return sub_names or [lic.value for lic in constants.LicenseTypes]

    @cached_property
    def LicenseTypes(self) -> constants.LicenseTypes:
        if len(list(self.licenses)) > 0:
            return Enum("ValidLicenseTypes", {item: item.replace("_", "-") for item in self.licenses}, type=str)
        else:  # pragma: no cover
            return constants.LicenseTypes

    @property
    def clients(self) -> Generator[CacheClient, None, None]:
        yield from self._get_all(Client, CacheClient)

    @property
    def cache_clients_by_mac(self) -> dict[str, dict[str, Any]]:
        """All Clients by MAC connected within the last 90 days

        This property is used by the cache to purge clients older than 90 days from cache

        Returns:
            dict[str,Document]: Client Dict keyed by MAC
            with any clients last connected > 90 days ago filtered out.
        """
        days = 90 if not self.config else self.config.cache_client_days
        return {
            c.mac: dict(c)
            for c in self.clients
            if c.last_connected is not None and not utils.older_than(c.last_connected, days)
        }

    @property
    def clients_by_mac(self) -> dict[str, CacheClient]:
        return {c.mac: c for c in self.clients}

    @property
    def mpsk_networks(self) -> Generator[CacheMpskNetwork, None, None]:
        yield from self._get_all(MPSKNetwork, CacheMpskNetwork)

    @property
    def mpsk(self) -> Generator[CacheMpsk, None, None]:
        yield from self._get_all(MPSK, CacheMpsk)

    @property
    def mpsk_by_id(self) -> dict[str, CacheMpsk]:
        return {m.id: m for m in self.mpsk}

    @property
    def portals(self) -> Generator[CachePortal, None, None]:
        yield from self._get_all(Portal, CachePortal)

    @property
    def portals_by_id(self) -> dict[str, CachePortal]:
        return {p.id: p for p in self.portals}

    @property
    def guests(self) -> Generator[CacheGuest, None, None]:
        yield from self._get_all(Guest, CacheGuest)

    @property
    def guests_by_id(self) -> dict[str, CacheGuest]:
        return {p.id: p for p in self.guests}

    @property
    def certs(self) -> Generator[CacheCert, None, None]:
        yield from self._get_all(Cert, lambda c: CacheCert(**c))  # TODO make others consistent with Cert of vice/versa re need to unpack.

    @property
    def certs_by_name(self) -> dict[str, CacheCert]:
        return {c.name: c for c in self.certs}

    @property
    def certs_by_md5(self) -> dict[str, CacheCert]:
        return {cert.md5_checksum: cert for cert in self.certs}

    @property
    def logs(self) -> Generator[CacheAuditLog, None, None]:  # TODO refactor to audit_logs
        yield from self._get_all(CentralAuditLog, CacheAuditLog)

    @property
    def events(self) -> Generator[CacheEvent, None, None]:
        yield from self._get_all(Event, CacheEvent)

    @property
    def event_ids(self) -> list[str]:  # list of int as str  # TODO no reason to store as str
        return [e.id for e in self.events]

    @property
    def templates(self) -> Generator[CacheTemplate, None, None]:
        yield from self._get_all(Template, CacheTemplate)

    @property
    def templates_by_name_group(self) -> dict[str, CacheTemplate]:
        return {
            f'{template.name}_{template.group}': template
            for template in self.templates
        }

    @property
    def floor_plan_aps(self) -> Generator[CacheFloorPlanAP, None, None]:
        return self._get_all(FloorPlanAP, CacheFloorPlanAP)

    @property
    def floor_plan_buildings(self) -> Generator[CacheBuilding]:
        return self._get_all(Building, CacheBuilding)

    @property
    def floor_plan_aps_by_serial(self) -> dict[str, CacheFloorPlanAP]:
        return {ap.serial: ap for ap in self.floor_plan_aps}

    @property
    def hook_data(self) -> list[dict[str, str | int | bool]]:
        return self._get_all(WebHookData, dict)

    @property
    def hook_active(self) -> list:
        return [h for h in self.hook_data if h and h["state"].lower() == "open"]

    async def get_hooks_by_serial(self, serial):
        with Session(self.engine) as session:
            start = time.perf_counter()
            stmt = select(WebHookData).where(WebHookData.device_id == serial.upper())
            matches: list[WebHookData] = session.scalars(stmt).all()
            end = time.perf_counter() - start
            log.debug(f"{len(matches)} fetched from wh_data table (Cache.get_hooks_by_serial) in {round(end - start, 3)}")

        return [m.to_dict() for m in matches]

    def fuzz_lookup(self, query_str: str, table: CacheTable, cache_object: CacheObject, field: str = "name", group: str = None, portal_id: str = None, dev_type: list[constants.LibAllDevTypes] = None) -> list[CacheTable]:  # pragma: no cover  Requires tty
        cache_items = self._get_all(table, cache_object)
        if not render.console.is_terminal or not cache_items:
            return []

        def _conditions(item: CacheObject, group: str = None, portal_id: str = None, dev_type: list[constants.LibAllDevTypes] = None) -> bool:
            if not any([group, portal_id, dev_type]):
                return True
            if group:
                return item.group == group
            if portal_id:
                return item.portal_id == portal_id
            if dev_type:
                return item.type in dev_type

        fuzz_resp = process.extract(
            query_str, [getattr(item, field) for item in cache_items if _conditions(item, group=group, portal_id=portal_id, dev_type=dev_type)], limit=1
        )
        matches = []
        if fuzz_resp:
            fuzz_match, fuzz_confidence = fuzz_resp[0]
            if fuzz_confidence >= 70 and render.confirm(prompt=f"Did you mean [green3]{fuzz_match}[/]?", abort=False):
                with Session(self.engine) as session:
                    start = time.perf_counter()
                    stmt = select(table).where(getattr(table, field) == fuzz_match)
                    matches: list[CacheTable] = session.scalars(stmt).all()
                    log.debug(f"{len(matches)} {table.__name__} fetched via fuzz lookup in {round(time.perf_counter() - start, 3)}")

        return matches

    # TODO remove cache.responses logic and use lru_cache, will need to add refresh: bool = False or use_cache: bool = True and clear_cache on self.refresh_xx_db funcs
    def get_devices_with_inventory(
        self,
        no_refresh: bool = False,
        inv_db: bool = None,
        dev_db: bool = None,
        device_type: constants.GenericDeviceTypes = None,
        assigned: bool = None,
        archived: bool = None,
        status: constants.DeviceStatus = None,
    ) -> list[Response] | Response:
        """Returns List of Response objects with data from Inventory and Monitoring

        Args:
            no_refresh (bool, optional): Used currently cached data, skip refresh of cache.
                Refresh will only occur if cache was not updated during this session.
                Setting no_refresh to True means it will not occur regardless.
                Defaults to False.
            inv_db (bool, optional): Update inventory cache. Defaults to None.
            dev_db (bool, optional): Update device (monitoring) cache. Defaults to None.
            device_type (Literal['ap', 'gw', 'switch'], optional): Filter devices by type:
                Valid Types: 'ap', 'gw', 'switch'.  'cx' and 'sw' also accepted, both will result in 'switch' which includes both types.
                Defalts to None (no Filter/All device types).
            status (Literal 'up', 'down', optional): Filter results by status.
                Inventory only devices (have never checked in, so lack status) are retained.
                Defaults to None.

        Returns:
            list[Response]: Response objects where output is list of dicts with
                            data from Inventory and Monitoring combined.
        """
        if not no_refresh:
            res = self.check_fresh(dev_db=dev_db or self.responses.dev is None, inv_db=inv_db or self.responses.inv is None, dev_type=device_type, assigned=assigned, archived=archived)
        else:
            res = [self.responses.dev or Response()]

        _inv_by_ser = self.inventory_by_serial if not self.responses.inv else {d["serial"]: d for d in self.responses.inv.output}
        # _dev_by_ser = {d["serial"]: d for d in self.responses.dev.output}  # Need to use the resp value not what was just stored in cache (self.devices_by_serial) as we don't store all fields
        _dev_by_ser = self.devices_by_serial if not self.responses.dev else {d["serial"]: d for d in self.responses.dev.output}

        if device_type:
            _dev_types = [device_type] if device_type != "switch" else ["cx", "sw", "mas"]
            _dev_by_ser = {serial: _dev_by_ser[serial] for serial in _dev_by_ser if _dev_by_ser[serial]["type"] in _dev_types}
            _inv_by_ser = {serial: _inv_by_ser[serial] for serial in _inv_by_ser if _inv_by_ser[serial]["type"] in _dev_types}

        if status:
            _dev_by_ser = {serial: _dev_by_ser[serial] for serial in _dev_by_ser if _dev_by_ser[serial]["status"] == status.capitalize()}
            _all_serials = list(_dev_by_ser.keys())
        else:
            _all_serials = set([*_inv_by_ser.keys(), *_dev_by_ser.keys()])

        if no_refresh:  # update inv cache for any devices that indicate status up but lack an inv entry (they are obviously in the inventory)
            inv_refresh_serials = [serial for serial in _dev_by_ser if _dev_by_ser[serial].get("status", "").lower() == "up" and serial not in _inv_by_ser]
            if inv_refresh_serials:
                inv_resp = asyncio.run(self.refresh_inv_db(dev_type=device_type, serial_numbers=inv_refresh_serials))
                if inv_resp.ok:
                    _inv_by_ser = {**_inv_by_ser, **{d["serial"]: d for d in inv_resp.output}}
                else:
                    log.error(f"Attempt to fetch [green]GreenLake[/] inventory data from {len(inv_refresh_serials)} devices that appear to be missing from cache failed ({inv_resp.error}).  Inventory data may be incomplete.", show=True, caption=True)
                    log.error(f"The following {len(inv_refresh_serials)} appear in monitoring cache with status Up, so should be in inventory cache.  Attempt to update inventory cache failed: ({inv_resp.error}).\n{inv_refresh_serials = }")

        combined = [
            {
                **_inv_by_ser.get(serial, {}),
                **_dev_by_ser.get(serial, {}),
                "model": _inv_by_ser.get(serial, {}).get("model", _dev_by_ser.get(serial, {}).get("model"))  # The model from inv is more concise, better for confirmation prompts
            } for serial in _all_serials
        ]

        # TODO this may be an issue if check_fresh has a failure, don't think it returns Response object
        resp: Response = min([r for r in res if r is not None], key=lambda x: x.rl)  # TODO update to use BatchResponse

        resp.output = combined
        # Both are None if a partial error occured in show all.  To test change url in-flight so one of the 3 calls fails
        try:
            resp.raw = {**self.responses.dev.raw, **self.responses.inv.raw}
        except AttributeError:
            if isinstance(resp, CombinedResponse):
                resp.raw = {**resp.raw, **{f.url.path: f.raw for f in resp.failed}}
            else:
                resp.raw = {"Error": "raw output not available due to partial failure."}
        return resp

    def _get_filtered_devices_w_inventory(self, refresh: bool = True, site: CacheSite = None, group: CacheGroup = None, not_group: CacheGroup = None, dev_type: constants.GroupDevTypes = None, not_dev_type: constants.GroupDevTypes = None, site_import: Path = None) -> list[dict[str, Any]]:
        resp = self.cache.get_devices_with_inventory(device_type=dev_type, no_refresh=not refresh)
        if not resp:
            log.error("Aborted.  Attempt to update the cache failed", caption=True)
            render.display_results(resp, exit_on_fail=True)

        if site or group:
            data = resp.output.copy()
            if site:
                data = [d for d in data if (d.get("site") or "") == site.name]
            if group:
                data = [d for d in data if (d.get("group_name", d.get("group")) or "") == group.name]
            if not_group:
                data = [d for d in data if (d.get("group_name", d.get("group")) or "") != not_group.name]

            if dev_type:
                data = [d for d in data if (d.get("type") or "") == dev_type]
            elif not_dev_type:
                data = [d for d in data if (d.get("type") or "") != not_dev_type]
        elif site_import:
            site_data = self._get_import_file(site_import, import_type="sites", text_ok=True)
            cache_sites = [self.cache.get_site_identifier(s["name"]) for s in site_data]
            data = [d for s in cache_sites for d in resp.output if (d.get("site") or "") == s.name]
        else:
            raise TypeError("missing 1 required argument.  At least one of group, site, or site_import is required.")

        return data

    def get_inv_mon_devs_from_cache(
        self,
        *,
        serial_numbers: list[str] | str = None,
        inv_db: bool = None,
        dev_db: bool = None,
        dev_type: constants.GenericDeviceTypes | list[constants.GenericDeviceTypes] = None,
        sites: str | list[str] = None,
        group: CacheGroup = None,
        not_group: CacheGroup = None,
        not_dev_type: constants.GroupDevTypes = None,
        assigned: bool = None,
        archived: bool = None,
        refresh: bool = False,
        refresh_on_fail: bool = True,
    ) -> list[MigrateDevice | CacheDevice | CacheInvDevice | None]:
        serial_numbers = serial_numbers and utils.listify(serial_numbers) or []
        sites = sites and utils.listify(sites) or []
        dev_type = dev_type and utils.expand_generic_dev_type(dev_type) or []

        if any([len(items) > 32_766 for items in [serial_numbers, sites] if items]):  # pragma: no cover
            render.econsole.print(f"{emoji.warn}  Number of lookups exceeds the max (32,766) allowed.  Reduce the number of serial_numbers or sites")
            raise typer.Exit(1)

        def _refresh(serials: list[str] = serial_numbers) -> None:
            res = BatchResponse(self.check_fresh(dev_db=dev_db or self.responses.dev is None, inv_db=inv_db or self.responses.inv is None, dev_type=dev_type, assigned=assigned, archived=archived, serial_numbers=serials))
            if not res.ok:
                log.error(f"{'Partial f' if res.passed else 'F'}ailure while updating the cache.  Aborting.", caption=True)
                render.display_results(res.failed, tablefmt="action", exit_on_fail=True)

        if refresh:
            _refresh()

        # if dev_type:
        #     dev_type = utils.expand_generic_dev_type(dev_type)

        expressions = []
        if serial_numbers:
            expressions += [Device.serial.in_(serial_numbers)]
        else:
            if sites:
                # sites = utils.listify(sites)
                # if len(sites) > 32_766:
                #     render.econsole.print(f"{emoji.warn}  {len(sites)} exceeds the max (32,766) allowed.  Reduce the number of sites migrated at a time.")
                #     raise typer.Exit(1)
                expressions += [Device.site.in_(sites)]
            if group:
                expressions += [Device.group == group.name]
            elif not_group:
                expressions += [Device.group != not_group.name]
            if dev_type:
                expressions += [Device.type.in_(dev_type)]
            elif not_dev_type:
                expressions += [~Device.type.in_(dev_type)]

        # This query will not return a result if the device is missing from either cache.  So it could be in devices (monitoring) but be missing from inventory or visa-versa... it will not return a result
        stmt = select(Device.name, Device.status, Device.type, InventoryDevice.model, Device.ip, Device.serial, Device.mac, InventoryDevice.id, Device.site, Device.group, InventoryDevice.subscription, InventoryDevice.assigned, InventoryDevice.archived, Device.swack_id).join(InventoryDevice).where(and_(*expressions))
        for idx in range(2):
            found = []
            with Session(self.engine) as session:
                with session.bind.connect() as connection:
                    mon_cache_result = connection.execute(stmt)
                    found = [MigrateDevice(dict(row)) for row in mon_cache_result.mappings()]
                    if not serial_numbers:
                        return found

            if len(serial_numbers) == len(found):
                return found

            if idx == 0 and not refresh:
                if refresh_on_fail:
                    not_found_serials = [s for s in serial_numbers if s not in [d.serial for d in found]]
                    _refresh(serials=not_found_serials)
                else:
                    break

        found_by_serial = {dev.serial: dev for dev in found}
        mon_cache_result = {serial: found_by_serial.get(serial) for serial in serial_numbers}
        not_found_serials = [serial for serial in mon_cache_result if mon_cache_result[serial] is None]
        mon_cache_stmt = select(Device).where(Device.serial.in_(not_found_serials))
        inv_cache_stmt = select(InventoryDevice).where(InventoryDevice.serial.in_(not_found_serials))
        with Session(self.engine) as session:
            with session.bind.connect() as connection:
                mon_cache_result = connection.execute(mon_cache_stmt)
                mon_cache_found = [CacheDevice(dict(row)) for row in mon_cache_result.mappings()]
                mon_cache_by_serial = {dev.serial: dev for dev in mon_cache_found}

                inv_cache_by_serial = {}
                if (len(found_by_serial) + len(mon_cache_by_serial)) != len(serial_numbers):
                    inv_cache_result = connection.execute(inv_cache_stmt)
                    inv_cache_found = [CacheInvDevice(dict(row)) for row in inv_cache_result.mappings()]
                    inv_cache_by_serial = {dev.serial: dev for dev in inv_cache_found}

        return [found_by_serial.get(serial, mon_cache_by_serial.get(serial, inv_cache_by_serial.get(serial))) for serial in serial_numbers]

    def bulk_inv_cache_lookup(
        self,
        *,
        serial_numbers: list[str] | str = None,
        glp_ids: list[str] | str = None,
        dev_type: constants.GenericDeviceTypes | list[constants.GenericDeviceTypes] = None,
        refresh: bool = False,
        refresh_on_fail: bool = True,
    ) -> list[CacheInvDevice | None]:
        serial_numbers = serial_numbers and utils.listify(serial_numbers) or []
        glp_ids = glp_ids and utils.listify(glp_ids) or []
        dev_type = dev_type and utils.expand_generic_dev_type(dev_type) or []
        unique_id_qry = True if any([serial_numbers, glp_ids]) else False

        if len([*serial_numbers, *glp_ids]) > 32_766:
            render.econsole.print(f"{emoji.warn}  Number of lookups exceeds the max (32,766) allowed.  Reduce the number of serial_numbers/glp_ids")
            raise typer.Exit(1)

        def _refresh() -> None:
            res = BatchResponse(self.check_fresh(inv_db=True, dev_type=dev_type, serial_numbers=serial_numbers))  # todo test and add id qry to get_devices
            if not res.ok:
                render.display_results(res.responses, tablefmt="action", exit_on_fail=True)

        expressions = []
        if dev_type:
            if unique_id_qry:
                raise ValueError("serial_numbers|glp_ids are device specific.  dev_type is only valid by itself.")
            expressions += [InventoryDevice.type.in_(dev_type)]
        elif serial_numbers:
            expressions += [InventoryDevice.serial.in_(serial_numbers)]
        elif glp_ids:
            expressions += [InventoryDevice.id.in_(glp_ids)]
        else:
            raise ValueError("dev_type, serial_numbers, or glp_ids required.")

        if refresh:
            _refresh()

        for idx in range(2):
            found = []
            stmt = select(InventoryDevice).where(or_(*expressions))
            with Session(self.engine) as session:
                with session.bind.connect() as connection:
                    result = connection.execute(stmt)
                    found = [CacheInvDevice(dict(row)) for row in result.mappings()]
                    if not unique_id_qry:
                        return found

            if len(serial_numbers) == len(found):
                break

            if not refresh_on_fail or refresh:
                break

            if idx == 0:
                _refresh()

        if serial_numbers:
            found_by_serial = {dev.serial: dev for dev in found}
            return [found_by_serial.get(serial) for serial in serial_numbers]

        found_by_id = {dev.id: dev for dev in found}
        return [found_by_id.get(id) for id in glp_ids]

    def bulk_dev_cache_lookup(
        self,
        *,
        serial_numbers: list[str] | str = None,
        # sites: list[str] | str = None,
        # groups: list[str] | str = None,
        dev_type: constants.GenericDeviceTypes | list[constants.GenericDeviceTypes] = None,
        refresh: bool = False,
        refresh_on_fail: bool = True,
    ) -> list[CacheDevice | None]:
        # serial_numbers required for now TODO add sites/groups (get all cache devs associated with... ) when needed for something
        serial_numbers = serial_numbers and utils.listify(serial_numbers) or []
        dev_type = dev_type and utils.expand_generic_dev_type(dev_type) or []
        unique_id_qry = True if serial_numbers else False

        if len(serial_numbers) > 32_766:
            render.econsole.print(f"{emoji.warn}  Number of lookups exceeds the max (32,766) allowed.  Reduce the number of serial_numbers")
            raise typer.Exit(1)

        def _refresh() -> None:
            res = BatchResponse(self.check_fresh(dev_db=True, dev_type=dev_type, serial_numbers=serial_numbers))  # todo test and add id qry to get_devices
            if not res.ok:
                render.display_results(res.responses, tablefmt="action", exit_on_fail=True)

        expressions = []
        if dev_type:
            if not unique_id_qry:  # We still leverage dev_type for more effecient cache refresh
                expressions += [Device.type.in_(dev_type)]

        if serial_numbers:
            expressions += [Device.serial.in_(serial_numbers)]
        else:
            raise ValueError("dev_type or serial_numbers required.")

        if refresh:
            _refresh()

        for idx in range(2):
            found = []
            stmt = select(Device).where(or_(*expressions))
            with Session(self.engine) as session:
                with session.bind.connect() as connection:
                    result = connection.execute(stmt)
                    found = [CacheDevice(dict(row)) for row in result.mappings()]
                    if not unique_id_qry:
                        return found

            if len(serial_numbers) == len(found):
                break

            if not refresh_on_fail or refresh:
                break

            if idx == 0:
                _refresh()

        found_by_serial = {dev.serial: dev for dev in found}
        return [found_by_serial.get(serial) for serial in serial_numbers]

    def bulk_site_cache_lookup(
        self,
        site_names: list[str] | str,
        *,
        refresh: bool = False,
        refresh_on_fail: bool = True,
    ) -> list[CacheSite | None]:
        site_names = utils.listify(site_names)

        if len(site_names) > 32_766:
            render.econsole.print(f"{emoji.warn}  Number of lookups exceeds the max (32,766) allowed.  Reduce the number of sites")
            raise typer.Exit(1)

        def _refresh() -> None:
            res = asyncio.run(self.refresh_site_db())
            if not res.ok:
                render.display_results(res, tablefmt="action", exit_on_fail=True)

        if refresh:
            _refresh()

        for idx in range(2):
            found = []
            stmt = select(Site).where(or_(Site.name.in_(site_names), func.lower(Site.name).in_(list(map(str.lower, site_names)))))
            with Session(self.engine) as session:
                with session.bind.connect() as connection:
                    result = connection.execute(stmt)
                    found = [CacheSite(dict(row)) for row in result.mappings()]

            if len(site_names) == len(found):
                break

            if not refresh_on_fail or refresh:
                break

            if idx == 0:
                _refresh()

        found_by_name = {site.name: site for site in found}
        found_by_name_lower = {site.name.lower(): site for site in found}
        return [found_by_name.get(name, found_by_name_lower.get(name.lower())) for name in site_names]

    @ensure_config
    def workspace_completion(self, incomplete: str):
        for ws in self.config.defined_workspaces:
            if ws.lower().startswith(incomplete.lower()):
                yield ws, self.config.data["workspaces"][ws].get("cluster") or ""

    @ensure_config
    def method_test_completion(self, incomplete: str, args: list[str] = []):  # pragma: no cover
        methods: list[str] = list(set(
            [d for svc in api.__dir__() if not svc.startswith("_") for d in getattr(api, svc).__dir__() if not d.startswith("_")]
        ))

        import importlib
        bpdir = Path(__file__).parent / "boilerplate"
        all_calls = [
            importlib.import_module(f"centralcli.{bpdir.name}.{f.stem}") for f in bpdir.iterdir()
            if not f.name.startswith("_") and f.suffix == ".py"
        ]
        client = ClientSession(self.config.classic.base_url)
        for m in all_calls:
            methods += [
                d for d in m.AllCalls(client).__dir__()
                if not d.startswith("__")
            ]

        for m in sorted(methods):
            if m.startswith(incomplete):
                yield m

    @ensure_config
    def smg_kw_completion(self, ctx: typer.Context, incomplete: str, args: list[str] = []):
        kwds = ["group", "mac", "serial"]
        out = []

        if not args:  # HACK click 8.x work-around now pinned at click 7.2 until resolved
            args = [v for k, v in ctx.params.items() if v and k != "workspace"]  # TODO ensure k is last item when v = incomplete

        if args[-1].lower() == "group":
            out = [m for m in self.group_completion(incomplete, args)]
            for m in out:
                yield m
        elif args[-1].lower() == "serial":
            out = ["|", "<SERIAL NUMBER>"]
            if incomplete:
                out.append(incomplete)
            for m in out:
                yield m
        elif args[-1].lower() == "mac":
            out = ["|", "<MAC ADDRESS>"]
            for m in out:
                yield m
        else:
            for kw in kwds:
                if kw not in args and kw.lower().startswith(incomplete):
                    yield kw

    def null_completion(self, incomplete: str):  # pragma: no cover
        incomplete = "NULL_COMPLETION"
        _ = incomplete
        for m in ["|", "<cr>"]:
            yield m

    @ensure_config
    def dev_completion(
        self,
        incomplete: str,
        args: list[str] = None
    ):
        dev_type = None
        if args:
            if args[-1].lower() in ["gateways", "clients", "server"]:
                dev_type = "gw"
            elif "dev-type" in args and len(args) > 1:
                dev_type = args[args.index("dev-type") + 1]
            elif args[-1].lower().startswith("switch"):
                dev_type = "switch"
            elif args[-1].lower() in ["aps", "ap"]:
                dev_type = "ap"

        match = self.get_dev_identifier(
            incomplete,
            dev_type=dev_type,
            completion=True,
        )
        out = []
        args = args or []
        if match:
            for m in sorted(match, key=lambda i: i.name):
                out += [m.get_completion(incomplete, args=args)]

        for m in out:
            yield m

    @ensure_config
    def dev_switch_completion(
        self,
        incomplete: str,
        args: list[str] = [],
    ) -> Iterator[tuple[str, str]]:
        """Device completion for returning matches that are switches (AOS-SW or CX)

        Args:
            incomplete (str): The last partial or full command before completion invoked.
            args (list[str], optional): The previous arguments/commands on CLI. Defaults to [].

        Yields:
            Iterator[tuple[str, str]]: Name and help_text for the device, or
                Returns None if config is invalid
        """
        match = self.get_dev_identifier(incomplete, dev_type="switch", completion=True)

        out = [] if not match else [c for c in [m.get_completion(incomplete, args=args) for m in sorted(match, key=lambda i: i.name)] if c is not None]

        for m in out:
            yield m

    def _dev_switch_by_type_completion(
        self,
        incomplete: str,
        args: list[str] = [],
        dev_type: Literal["cx", "sw"] = "cx",
    ) -> Iterator[tuple[str, str]]:
        """Device completion for returning matches that are of specific switch type (cx by default)

        Args:
            incomplete (str): The last partial or full command before completion invoked.
            args (list[str], optional): The previous arguments/commands on CLI. Defaults to [].

        Yields:
            Iterator[tuple[str, str]]: Name and help_text for the device, or
                Returns None if config is invalid
        """
        match = self.get_dev_identifier(incomplete, dev_type=[dev_type], completion=True)

        out = [] if not match else [c for c in [m.get_completion(incomplete, args=args) for m in sorted(match, key=lambda i: i.name)] if c is not None]

        for m in out:
            yield m

    @ensure_config
    def dev_cx_completion(
            self,
            incomplete: str,
            args: list[str] = [],
    ) -> Iterator[tuple[str, str]]:
        yield from self._dev_switch_by_type_completion(incomplete=incomplete, args=args, dev_type="cx")

    @ensure_config
    def dev_sw_completion(
            self,
            incomplete: str,
            args: list[str] = [],
    ) -> Iterator[tuple[str, str]]:
        yield from self._dev_switch_by_type_completion(incomplete=incomplete, args=args, dev_type="sw")

    @ensure_config
    def dev_ap_gw_sw_completion(
        self,
        ctx: typer.Context,
        incomplete: str,
        args: list[str] = [],
    ) -> Iterator[tuple[str, str]]:
        """Device completion for returning matches that are ap, gw, or AOS-SW

        Args:
            incomplete (str): The last partial or full command before completion invoked.
            args (list[str], optional): The previous arguments/commands on CLI. Defaults to [].

        Yields:
            Iterator[tuple[str, str]]: Name and help_text for the device, or
                Returns None if config is invalid
        """
        yield from self.dev_ap_gw_completion(ctx, incomplete, args=args)
        yield from self.dev_sw_completion(incomplete, args=args)

    @ensure_config
    def mpsk_network_completion(
        self,
        ctx: typer.Context,
        incomplete: str,
        args: list[str] = None,
    ):
        match = self.get_mpsk_network_identifier(
            incomplete,
            completion=True,
        )
        out = []
        args = args or ctx.params.values()  # HACK as args stopped working / seems to be passing args typer 0.10.0 / click 7.1.2
        if match:
            for m in sorted(match, key=lambda i: i.name):
                if str(m.id).startswith(incomplete):
                    out += [tuple([m.id, m.name])]
                elif m.name not in args:
                    out += [tuple([m.name, m.id])]

        for m in out:
            yield m

    @ensure_config
    def portal_completion(
        self,
        ctx: typer.Context,
        incomplete: str,
        args: list[str] = None,
    ):
        match: list[CachePortal] = self.get_portal_identifier(
            incomplete,
            completion=True,
        )
        args = args or [item for k, v in ctx.params.items() if v for item in [k, v]]

        out = []
        if match:
            # remove items that are already on the command line
            match = [m for m in match if m.name not in args]
            for m in sorted(match, key=lambda i: i.name):
                if str(m.id).startswith(incomplete):
                    out += [tuple([m.id, m.help_text])]
                elif m.name not in args:
                    out += [tuple([m.name, m.help_text])]

        for m in out:
            yield m

    @ensure_config
    def guest_completion(
        self,
        ctx: typer.Context,
        incomplete: str = "",
        args: list[str] = None,
    ):
        match = self.get_guest_identifier(
            incomplete,
            completion=True,
        )
        out = []
        args = args or [item for k, v in ctx.params.items() if v for item in [k, v]]

        if match:
            # remove items that are already on the command line
            for m in sorted(match, key=lambda i: i.name):
                if m.email and m.email.startswith(incomplete) and m.email not in args:
                    out += [tuple([m.email, m.help_text])]
                elif m.phone and m.phone.startswith(incomplete.lstrip("+")) and m.phone.lstrip("+") not in args:
                    out += [tuple([m.phone, m.help_text])]
                elif m.id.startswith(incomplete) and m.id not in args:
                    out += [tuple([m.id, m.help_text])]
                elif m.name not in args:
                    out += [tuple([m.name, m.help_text])]

        for m in out:
            yield m

    @ensure_config
    def cert_completion(
        self,
        ctx: typer.Context,
        incomplete: str = "",
        args: list[str] = None,
    ):
        match = self.get_cert_identifier(
            incomplete,
            completion=True,
        )
        out = []
        args = args or [item for k, v in ctx.params.items() if v for item in [k, v]]

        if match:
            for m in sorted(match, key=lambda i: i.name):
                if m.md5_checksum.startswith(incomplete) and m.md5_checksum not in args:
                    out += [tuple([m.md5_checksum, m.help_text])]
                elif m.name not in args:
                    out += [tuple([m.name, m.help_text])]

        for m in out:
            yield m

    @ensure_config
    def sub_completion(
        self,
        ctx: typer.Context,
        incomplete: str = None,
        args: list[str] = None,
    ):
        incomplete = incomplete or ""
        match: list[CacheSub] = self.get_sub_identifier(
            incomplete,
            completion=True,
        )
        args = args or [item for k, v in ctx.params.items() if v for item in [k, v]]

        out = []
        if match:
            for m in sorted(match, key=lambda i: i.name):
                if m.key.startswith(incomplete) and m.key not in args:
                    out += [tuple([m.key, m.help_text])]
                elif m.id.startswith(incomplete) and m.id not in args:
                    out += [tuple([m.id, m.help_text])]
                elif m.name not in args:
                    out += [tuple([m.name, m.help_text])]

        for m in out:
            yield m

    @ensure_config
    def dev_kwarg_completion(
        self,
        ctx: typer.Context,
        incomplete: str,
        args: list[str] = None,
    ) -> Iterator[tuple[str, str]]:
        """Completion for commands that allow a list of devices followed by group/site.

        i.e. cencli move dev1 dev2 dev3 site site_name group group_name

        Args:
            ctx (typer.Context): Provided automatically by typer
            incomplete (str): The incomplete word for autocompletion
            args (list[str], optional): The prev args passed into the command.

        Yields:
            Iterator[tuple[str, str]]: Matching completion string, help text, or
                Returns None if config is invalid
        """
        if not args:  # pragma: no cover # HACK resolves click 8.x issue now pinned to 7.2 until fixed upstream
            args = [k for k, v in ctx.params.items() if v and k[:2] not in ["kw", "va"]]
            args += [v for k, v in ctx.params.items() if v and k[:2] in ["kw", "va"]]

        if args and args[-1].lower() == "group":
            yield from self.group_completion(incomplete, args)

        elif args and args[-1].lower() == "site":
            yield from self.site_completion(ctx, incomplete, args)

        elif args and args[-1].lower() == "ap":
            yield from self.dev_completion(incomplete, args)

        else:
            out = []
            if len(args) > 1:
                if "site" not in args and "site".startswith(incomplete.lower()):
                    _help = "move device(s) to a different site" if ctx.info_name == "move" else f"{ctx.info_name} ... site"  # TODO the fallback ... need to check which commands use this.
                    out += [("site", _help)]
                if "group" not in args and "group".startswith(incomplete.lower()):
                    _help = "move device(s) to a different group" if ctx.info_name == "move" else f"{ctx.info_name} ... group"  # TODO the fallback ... need to check which commands use this.
                    out += [("group", _help)]

            if "site" not in args and "group" not in args:
                out = [*out, *[m for m in self.dev_completion(incomplete, args)]]

            for m in out:
                yield m if isinstance(m, tuple) else (m, f"{ctx.info_name} ... {m}")

    @ensure_config
    def dev_ap_completion(
        self,
        # ctx: typer.Context,
        incomplete: str,
        args: list[str] = None,
    ) -> Iterator[tuple[str, str]]:
        """Completion for argument where only APs are valid.

        Args:
            incomplete (str): The last partial or full command before completion invoked.
            args (list[str], optional): The previous arguments/commands on CLI. Defaults to None.

        Yields:
            Iterator[tuple[str, str]]: Name and help_text for the device, or
                Returns None if config is invalid
        """
        match: list[CacheDevice] = self.get_dev_identifier(incomplete, dev_type=["ap"], completion=True)

        out = [] if not match else [c for c in [m.get_completion(incomplete, args=args) for m in sorted(match, key=lambda i: i.name)] if c is not None]

        for m in out:
            yield m

    # TODO put client names with spaces in quotes
    # TODO does not appear to be used by any command
    @ensure_config
    def dev_client_completion(
        self,
        ctx: typer.Context,
        incomplete: str,
        args: list[str] = [],
    ) -> Iterator[tuple[str, str]]:
        """Completion for client output.

        Returns only devices that apply based on filter provided in command, defaults to clients
        on both APs and switches (wires/wireless), but returns applicable devices if "wireless" or
        "wired" filter is used.

        Args:
            incomplete (str): The last partial or full command before completion invoked.
            args (list[str], optional): The previous arguments/commands on CLI. Defaults to [].

        Yields:
            Iterator[tuple[str, str]]: Tuple with completion and help text, or
                Returns None if config is invalid
        """
        if ctx.params.get("wireless"):
            gen = self.dev_ap_completion
        elif ctx.params.get("wired"):
            gen = self.dev_switch_completion
        else:
            gen = self.dev_switch_ap_completion

        yield from gen(incomplete, args)

    @ensure_config
    def dev_switch_ap_completion(
        self,
        incomplete: str,
        args: list[str] = [],
    ) -> Iterator[tuple[str, str]]:
        """Device completion for returning matches that are either switch or AP

        Args:
            incomplete (str): The last partial or full command before completion invoked.
            args (list[str], optional): The previous arguments/commands on CLI.

        Yields:
            Iterator[tuple[str, str]]: Yields Tuple with completion and help text, or
                Returns None if config is invalid
        """
        match: list[CacheDevice] = self.get_dev_identifier(incomplete, dev_type=["switch", "ap"], completion=True)

        out = [] if not match else [c for c in [m.get_completion(incomplete, args=args) for m in sorted(match, key=lambda i: i.name)] if c is not None]

        for m in out:
            yield m

    @ensure_config
    def dev_ap_gw_completion(
        self,
        ctx: typer.Context,
        incomplete: str,
        args: list[str] = None,
    ) -> Iterator[tuple[str, str]]:
        """Device completion that returns only ap and gw.

        Args:
            incomplete (str): The last partial or full command before completion invoked.
            args (list[str], optional): The previous arguments/commands on CLI. Defaults to None.

        Yields:
            Iterator[tuple[str, str]]: Yields Tuple with completion and help text, or
                Returns None if config is invalid
        """
        # Prevents device completion for cencli show config self/cencli
        command_paths = ["cencli show config", "cencli update config"]
        if ctx.command_path in command_paths and ctx.params.get("group_dev", "") in ["cencli", "self"]:
            return

        yield from self.dev_ap_completion(incomplete, args=args)
        yield from self.dev_gw_completion(incomplete, args=args)

    @ensure_config
    def dev_switch_gw_completion(
        self,
        incomplete: str,
        args: list[str] = None,
    ) -> Iterator[tuple[str, str]]:
        """Device completion that returns only switches and gateways.

        Args:
            incomplete (str): The last partial or full command before completion invoked.
            args (list[str], optional): The previous arguments/commands on CLI. Defaults to None.

        Yields:
            Iterator[tuple[str, str]]: Name and help_text for the device, or
                Returns None if config is invalid
        """
        match = self.get_dev_identifier(incomplete, dev_type=["switch", "gw"], completion=True)

        out = [] if not match else [c for c in [m.get_completion(incomplete, args=args) for m in sorted(match, key=lambda i: i.name)] if c is not None]

        for m in out:
            yield m

    @ensure_config
    def dev_gw_completion(
        self,
        incomplete: str,
        args: list[str] = None,
    ) -> Iterator[tuple[str, str]]:
        """Completion for device idens where only gateways are valid.

        Args:
            incomplete (str): The last partial or full command before completion invoked.
            args (list[str], optional): The previous arguments/commands on CLI. Defaults to None.

        Yields:
            Iterator[tuple[str, str]]: Name and help_text for the device, or
                Returns None if config is invalid
        """
        match = self.get_dev_identifier(incomplete, dev_type="gw", completion=True)

        out = [] if not match else [c for c in [m.get_completion(incomplete, args=args) for m in sorted(match, key=lambda i: i.name)] if c is not None]

        for m in out:
            yield m

    @overload
    def get_cert_identifier(
        self,
        query_str: str,
        completion: Literal[True],
    ) -> list[CacheCert]: ...

    @overload
    def get_cert_identifier(
        self,
        query_str: str,
    ) -> CacheCert: ...

    @overload
    def get_cert_identifier(
        self,
        query_str: str,
        retry: Literal[False]
    ) -> None | CacheCert: ...

    def get_cert_identifier(
        self,
        query_str: str,
        retry: bool = True,
        completion: bool = False,
        silent: bool = False,
    ) -> CacheCert | list[CacheCert] | None:
        """Common Cache Lookups.  Currently only used by Cert Lookups"""
        start = time.perf_counter()
        retry = False if completion else retry
        if not query_str and completion:
            return list(self.certs)

        statements = [
            select(Cert).where(or_(Cert.name == query_str, Cert.md5_checksum == query_str, Cert.name.like(query_str))),
            select(Cert).where(or_(func.lower(Cert.name) == func.lower(query_str))),  # case insensitive
            select(Cert).where(or_(Cert.name.istartswith(query_str.replace("-", "_")), Cert.md5_checksum.istartswith(query_str))),
        ]

        matches: list[Cert] = []
        out: list[CacheCert] = []
        for _ in range(0, 2 if retry else 1):
            with Session(self.engine) as session:
                for stmt in statements:
                    matches = session.scalars(stmt).all()
                    if matches:
                        break

            if retry and not matches and self.responses.cert is None:
                econsole.print(f"{emoji.warn} [bright_red]No Match found for[/] [cyan]{query_str}[/].")
                if FUZZ and self.certs and not silent:  # pragma: no cover requires tty
                    matches = self.fuzz_lookup(query_str, table=Cert, cache_object=CacheCert)
                if not matches:
                    econsole.print(":arrows_clockwise: Updating certificate cache")
                    api.session.request(self.refresh_cert_db)
            if matches:
                out = [CacheCert(**c.to_dict()) for c in matches]
                break

        log.debug(f"get_cert_identifier found {len(out)} certificate matches in {round(time.perf_counter() - start, 3)}s")
        if out:
            if completion:
                return out

            if len(out) > 1:  # pragma: no cover requires tty
                out = self.handle_multi_match(
                    out,
                    query_str=query_str,
                    query_type="certificate",
                )

            return out[0]

        log.error(f"Unable to gather certificate from provided identifier {query_str}", show=not silent, log=silent)
        if retry:
            raise typer.Exit(1)  # no use case for exit_on_fail

    @overload
    def get_guest_identifier(
        self,
        query_str: str,
        completion: bool = True,
    ) -> list[CacheGuest]: ...

    @overload
    def get_guest_identifier(
        self,
        query_str: str,
        portal_id: str = None,
        retry: bool = True,
        completion: bool = False,
        silent: bool = False,
    ) -> CacheGuest: ...

    def get_guest_identifier(
        self,
        query_str: str,
        portal_id: str = None,
        retry: bool = True,
        completion: bool = False,
        silent: bool = False,
    ) -> CacheGuest | list[CacheGuest]:
        """Get guest info from Guest Cache"""
        start = time.perf_counter()
        retry = False if completion else retry
        if not query_str and completion:
            return list(self.guests)

        _phone = "".join([d for d in query_str if d.isdigit()])
        statements = [
            select(Guest).where(or_(Guest.name == query_str, Guest.email == query_str, Guest.phone == query_str, Guest.id == query_str)),  # exact match
            select(Guest).where(or_(func.lower(Guest.name) == func.lower(query_str), func.lower(Guest.email) == func.lower(query_str), func.lower(Guest.id) == func.lower(query_str))),  # case insensitive
            select(Guest).where(or_(Guest.name.istartswith(query_str), Guest.email.istartswith(query_str), Guest.id.istartswith(query_str))),  # case insensitive startswith match
            select(Guest).where(Guest.name.istartswith(query_str.replace("-", "_"))),  # case insensitive startswith ignore -_ match _ is wildcard for istartswith
        ]

        matches: list[Guest] = []
        all_matches: list[Guest] = []
        out: list[CacheGuest] = []
        for _ in range(0, 2 if retry else 1):
            with Session(self.engine) as session:
                for stmt in statements:
                    matches = session.scalars(stmt).all()
                    if matches:
                        break

            if not matches and _phone:  # phone with only last 10 digits (strip country code)... This is not a db lookup it fetches all values
                matches = [Guest(**m) for m in self.guests if m.phone and "".join([d for d in m.phone if d.isdigit()][::-1][0:10][::-1]).startswith("".join(_phone[::-1][0:10][::-1]))]

            if matches and portal_id:
                all_matches: list[Guest] = matches.copy()
                matches = [d for d in all_matches if d.portal_id == portal_id]

            if retry and not matches and self.responses.guest is None:
                econsole.print(f"{emoji.warn} [bright_red]No Match found for[/] [cyan]{query_str}[/].")
                if FUZZ and self.guests and not silent:  # pragma: no cover requires tty
                    matches = self.fuzz_lookup(query_str, table=Guest, cache_object=CacheGuest, portal_id=portal_id)
                if not matches:
                    if not portal_id:
                        econsole.print(f"{emoji.warn} Unable to gather guest from provided identifier {query_str}.  Use [cyan]cencli show guest <PORTAL>[/] to update cache.")
                        raise typer.Exit(1)
                    econsole.print(":arrows_clockwise: Updating guest Cache")
                    api.session.request(self.refresh_guest_db, portal_id=portal_id)
            if matches:
                out = [CacheGuest(g.to_dict(), cache=self) for g in matches]
                break

        log.debug(f"get_guest_identifier found {len(matches)} in {round(time.perf_counter() - start, 3)}s")
        if out:
            if completion:
                return out

            if len(out) > 1:  # pragma: no cover requires tty
                out = self.handle_multi_match(
                    out,
                    query_str=query_str,
                    query_type="guest",
                )

            return out[0]

        log.error(f"Unable to gather guest from provided identifier {query_str}", show=not silent, log=silent)
        if retry:
            if all_matches:
                log.error(
                    f"The Following {len(all_matches)} guest{'s' if len(out) > 1 else ''} matched: {utils.summarize_list([CacheGuest(m.to_dict(), cache=self) for m in all_matches], max=10)} [red]Excluded[/] as they are not associated with portal id [cyan]{portal_id}[/]",
                    show=True,
                )
            raise typer.Exit(1)  # No use case requiring exit_on_fail

    @staticmethod
    def _cencli_self(ctx: typer.Context, incomplete: str, args: tuple[str]) -> tuple[list[tuple[str, str]], list[str]]:
        word = "self" if "self".startswith(incomplete) else "cencli"
        if args:
            if " ".join(args).lower() in ["show config", "update config"] and word.startswith(incomplete):
                return [(word, f"{'show' if 'show' in args else 'update'} cencli configuration")], args
        elif ctx is not None:
            args = [a for a in ctx.params.values() if a is not None]
            if ctx.command_path in ["cencli show config", "cencli update config"] and ctx.params.get("group_dev") is None:  # typer not sending args fix
                if word.startswith(incomplete):
                    action = 'show' if ctx.command_path == 'cencli show config' else 'update'
                    return [(word, f"{action} cencli configuration")], args
        return [[], args]

    # FIXME not completing partial serial number is zsh get_dev_completion appears to return as expected
    # works in BASH and powershell
    def _group_dev_completion(
        self,
        incomplete: str,
        ctx: typer.Context = None,
        dev_type: constants.LibAllDevTypes | list[constants.LibAllDevTypes] = None,
        swack: bool = False,
        args: list[str] = None,
    ) -> Iterator[tuple[str, str]]:
        """Completion for argument that can be either group or device.

        Args:
            ctx (typer.Context): The click/typer Context.
            incomplete (str): The last partial or full command before completion invoked.
            dev_type: (str, optional): One of "ap", "cx", "sw", "switch", or "gw"
                where "switch" is both switch types.  Defaults to None (all device types)
            swack (bool, optional): If there are multiple matches (stack) return only the conductor as a match.
            args (list[str], optional): The previous arguments/commands on CLI. Defaults to None.

        Yields:
            Iterator[tuple[str, str]]: Name and help_text for the device, or
                Returns None if config is invalid
        """
        # Add cencli as option to show and update config commands (update not implememnted yet)
        utils.listify(dev_type)
        out, args = self._cencli_self(ctx, incomplete, args)

        group_out = self.group_completion(incomplete=incomplete, args=args)
        group_out = group_out if not group_out else list(group_out)
        if group_out and dev_type:
            cache_groups = [self.get_group_identifier(g[0]) for g in group_out]
            group_out = [complete_group for complete_group, cache_group in zip(group_out, cache_groups) if any([t in cache_group.allowed_types for t in dev_type])]
        if group_out:
            out += group_out

        if not bool([t for t in out if t[0] == incomplete]):  # group had exact match no need for dev
            match = self.get_dev_identifier(incomplete, dev_type=dev_type, swack=swack, completion=True)
            if match:
                out += [c for c in [m.get_completion(incomplete, args=args) for m in sorted(match, key=lambda i: i.name)] if c is not None]

        for m in out:
            yield m

    @ensure_config
    def group_dev_completion(
        self,
        ctx: typer.Context,
        incomplete: str,
        args: list[str] = None,
    ) -> Iterator[tuple[str, str]]:
        """Completion for argument that can be either group or device.

        Args:
            ctx (typer.Context): The click/typer Context.
            incomplete (str): The last partial or full command before completion invoked.
            args (list[str], optional): The previous arguments/commands on CLI. Defaults to None.

        Yields:
            Iterator[tuple[str, str]]: Name and help_text for the device, or
                Returns None if config is invalid
        """
        yield from self._group_dev_completion(incomplete, ctx=ctx, args=args)

    @ensure_config
    def group_dev_ap_gw_completion(
        self,
        ctx: typer.Context,
        incomplete: str,
        args: list[str] = None,
    ) -> Iterator[tuple[str, str]]:
        """Completion for argument that can be either group or device.

        Args:
            incomplete (str): The last partial or full command before completion invoked.
            args (list[str], optional): The previous arguments/commands on CLI. Defaults to None.

        Yields:
            Iterator[tuple[str, str]]: Name and help_text for the device, or
                Returns None if config is invalid
        """
        yield from self._group_dev_completion(incomplete, ctx=ctx, dev_type=["ap", "gw"], args=args)

    # TODO NOT USED???
    @ensure_config
    def group_dev_gw_completion(
        self,
        incomplete: str,
        args: list[str] = None,
    ) -> Iterator[tuple[str, str]]:  # pragma: no cover  This isn't used ... check if it was created with the intent to use it but never referenced
        """Completion for argument that can be either group or a gateway.

        Args:
            incomplete (str): The last partial or full command before completion invoked.
            args (list[str], optional): The previous arguments/commands on CLI. Defaults to None.

        Yields:
            Iterator[tuple[str, str]]: Name and help_text for the device, or
                Returns None if config is invalid
        """
        match: list[CacheDevice | CacheGroup] = self.get_identifier(incomplete, ["group", "dev"], device_type="gw", completion=True)

        out = []
        if match:
            for m in sorted(match, key=lambda i: i.name):
                out += [tuple([m.name, m.help_text])]

        for m in out:
            yield m[0], m[1]

    # FIXME completion doesn't pop args need ctx: typer.Context and reference ctx.params which is dict?
    @ensure_config
    def send_cmds_completion(
        self,
        ctx: typer.Context,
        incomplete: str,
        args: list[str] = [],
    ) -> Iterator[tuple[str, str]]:
        """Completion for argument that can be either group, site, or a gateway or keyword "commands".

        Args:
            incomplete (str): The last partial or full command before completion invoked.
            args (list[str], optional): The previous arguments/commands on CLI. Defaults to [].

        Yields:
            Iterator[tuple[str, str]]: Name and help_text for the device, or
                Returns None if config is invalid
        """
        if ctx.params.get("nodes") or ctx.params.get("kw1") == "all":
            yield "commands"
        elif ctx.params.get("kw1") in ["commands", "file"]:
            yield None  # force shell path completion
        elif ctx.params.get("kw1") not in ["group", "site", "device"]:
            yield "commands"
        else:
            if ctx.params.get("kw1") == "group":
                db = "group"
            elif ctx.params.get("kw1") == "site":
                db = "site"
            else:
                db = "dev"

            match: list[CacheDevice] | list[CacheGroup] | list[CacheSite] = self.get_identifier(incomplete, [db], device_type="gw", completion=True)

            out = []
            if match:
                for m in sorted(match, key=lambda i: i.name):
                    out += [tuple([m.name if " " not in m.name else f"'{m.name}'", m.help_text])]

                for m in out:
                    yield m[0], m[1]

    @ensure_config
    def group_completion(
        self,
        incomplete: str,
        args: list[str] = [],
    ) -> Iterator[tuple[str, str]]:
        """Completion for groups (by name).

        Args:
            incomplete (str): The last partial or full command before completion invoked.
            args (list[str], optional): The previous arguments/commands on CLI. Defaults to [].

        Yields:
            Iterator[tuple[str, str]]: Name and help_text for the group, or
                Returns None if config is invalid
        """
        match = self.get_group_identifier(
            incomplete,
            completion=True,
        )
        out = []
        if match:
            for m in sorted(match, key=lambda i: i.name):
                if m.name not in args:
                    out += [tuple([m.name, m.help_text])]
                    # out += [tuple([m.name if " " not in m.name else f"'{m.name}'", m.help_text])] # FIXME case insensitive and group completion now broken used to work
                    # FIXME zsh is displaying "name name name --help-text"  (name x 3 the help text on each line)

        for m in out:
            yield m

    @ensure_config
    def template_group_completion(
        self,
        incomplete: str,
        args: list[str] = [],
    ) -> Iterator[tuple[str, str]]:
        """Completion for template groups (by name).

        Args:
            incomplete (str): The last partial or full command before completion invoked.
            args (list[str], optional): The previous arguments/commands on CLI. Defaults to [].

        Yields:
            Iterator[tuple[str, str]]: Name and help_text for the group, or
                Returns None if config is invalid
        """
        all_match = self.get_group_identifier(
            incomplete,
            completion=True,
        )
        match = [m for m in all_match if m.wired_tg or m.wlan_tg]
        out = []
        if match:
            for m in sorted(match, key=lambda i: i.name):
                if m.name not in args:
                    out += [tuple([m.name, m.help_text])]

        for m in out:
            yield m

    @ensure_config
    def ap_group_completion(
        self,
        incomplete: str,
        args: list[str] = [],
    ) -> Iterator[tuple[str, str]]:
        """Completion for AP groups (by name).

        Args:
            incomplete (str): The last partial or full command before completion invoked.
            args (list[str], optional): The previous arguments/commands on CLI. Defaults to [].

        Yields:
            Iterator[tuple[str, str]]: Name and help_text for the group, or
                Returns None if config is invalid
        """
        match = self.get_group_identifier(
            incomplete,
            completion=True,
            dev_type=["ap"],
        )

        out = []
        if match:
            for m in sorted(match, key=lambda i: i.name):
                if m.name not in args:
                    out += [tuple([m.name, m.help_text])]

        for m in out:
            yield m

    @ensure_config
    def label_completion(
        self,
        ctx: typer.Context,
        incomplete: str,
        args: list[str] = [],
    ) -> Iterator[tuple[str, str]]:
        """Completion for labels.

        Args:
            incomplete (str): The last partial or full command before completion invoked.
            args (list[str], optional): The previous arguments/commands on CLI. Defaults to [].

        Yields:
            Iterator[tuple[str, str]]:  Name and help_text for the label, or
                Returns None if config is invalid
        """
        incomplete, pfx = _handle_multi_word_incomplete(incomplete)
        match: list[CacheLabel] = self.get_label_identifier(
            incomplete,
            completion=True,
        )

        out = []
        args = args or [item for k, v in ctx.params.items() if v for item in [k, v]]
        if match:
            match = [m for m in match if m.name not in args and str(m.id) not in args]
            for m in sorted(match, key=lambda i: i.name):
                if str(m.id).startswith(incomplete):
                    out += [(str(m.id), m.help_text)]
                else:
                    out += [m.get_completion(pfx=pfx)]  # TODO do this for others

        for m in out:
            yield m

    @ensure_config
    def client_completion(
        self,
        ctx: typer.Context,
        incomplete: str,
        args: list[str] = None,
    ) -> Iterator[tuple[str, str]]:
        """Completion for clients.

        Args:
            ctx (typer.Context): Provided automatically by typer
            incomplete (str): The last partial or full command before completion invoked.
            args (list[str], optional): The previous arguments/commands on CLI. Defaults to None.

        Yields:
            Iterator[tuple[str, str]]: Name and help_text for the client, or
                Returns None if config is invalid
        """
        incomplete, pfx = _handle_multi_word_incomplete(incomplete)
        match = self.get_client_identifier(
            incomplete,
            completion=True,
        )
        out = []
        args = args or []
        if match:
            # filter by type if we can gather type from context
            if ctx.params.get("wireless") or ctx.params.get("wired"):
                match = [m for m in match if m.type == f"{'wireless' if ctx.params.get('wireless') else 'wired'}"]
            # remove clients that are already on the command line
            match = [m for m in match if m.name not in args]
            for c in sorted(match, key=lambda i: i.name):
                if c.name.lower().startswith(incomplete.lower()):
                    if pfx == '"':
                        out += [(f'"{c.name}"', c.help_text)]
                    elif pfx == "'":
                        out += [(f"'{c.name}'", c.help_text)]
                    else:
                        out += [(c.name if " " not in c.name else f"'{c.name}'", c.help_text)]
                elif utils.Mac(c.mac).clean.startswith(utils.Mac(incomplete).clean):
                    out += [(c.mac, c.help_text)]
                elif c.ip.startswith(incomplete):
                    out += [(c.ip, c.help_text)]
                else:  # pragma: no cover
                    log.warning(f"DEV WARNING FailSafe Match hit in cache.client_completion {incomplete = }")
                    out += [(c.name, f'{c.help_text} FailSafe Match')]  # failsafe, shouldn't hit

        for c in out:
            yield c[0].replace(":", "-"), c[1]  # TODO completion behavior has changed.  This works-around issue bash doesn't complete past 00: and zsh treats each octet as a dev name when : is used.

    @ensure_config
    def event_log_completion(
        self,
        incomplete: str,
        args: list[str] = None,
    ) -> Iterator[tuple[str, str]]:
        """Completion for events.

        Args:
            incomplete (str): The last partial or full command before completion invoked.
            args (list[str], optional): The previous arguments/commands on CLI. Defaults to [].

        Yields:
            Iterator[tuple[str, str]]: Value and help_text for the event, or
                Returns None if config is invalid
        """
        _completion: list[tuple[str, str]] = [
            ("cencli", "Show cencli logs (alias for self)"),
            ("self", "Show cencli logs"),
            ("pytest", "Show cencli test run logs"),
            *[(x['id'], f"{x['id']}|{x['device'].split('Group:')[0].rstrip()}") for x in self.events]
        ]

        if incomplete == "":
            for m in _completion:
                yield m[0], m[1]

        else:
            args = args or []
            for m in _completion:
                if m[0].startswith(incomplete) and m[0] not in args:
                    yield m

    @ensure_config
    def audit_log_completion(
        self,
        incomplete: str,
        args: list[str] = None,
    ) -> Iterator[tuple[str, str]]:
        """Completion for audit event logs.

        Args:
            incomplete (str): The last partial or full command before completion invoked.
            args (list[str], optional): The previous arguments/commands on CLI. Defaults to [].

        Yields:
            Iterator[tuple[str, str]]: Value and help_text for the event, or
                Returns None if config is invalid
        """
        if incomplete == "":
            for m in self.logs:
                yield m["id"]
        else:
            for log in self.logs:
                if str(log["id"]).startswith(incomplete):
                    yield log["id"]

    @ensure_config
    def site_completion(
        self,
        ctx: typer.Context,
        incomplete: str,
        args: list[str] = None,
    ) -> Iterator[tuple[str, str]]:
        """Completion for sites.

        Args:
            incomplete (str): The last partial or full command before completion invoked.
            args (list[str], optional): The previous arguments/commands on CLI. Defaults to None.

        Yields:
            Iterator[tuple[str, str]]: Name and help_text for the site, or
                Returns None if config is invalid
        """
        args = args or [item for k, v in ctx.params.items() if v for item in [k, v]]

        match = self.get_site_identifier(
            incomplete.replace('"', "").replace("'", ""),
            completion=True,
        )

        out = []
        if match:
            for m in sorted(match, key=lambda i: i.name):
                match_attrs = [a for a in [m.name, m.id, m.address, m.city, m.state, m.zip] if a]
                if all([attr not in args for attr in match_attrs]):
                    matched_attribute = [attr for attr in match_attrs if str(attr).startswith(incomplete)]
                    # err_console.print(f"\n{match_attrs=}, {matched_attribute=}, {incomplete=}")  # DEBUG completion
                    matched_attribute = m.name if len(matched_attribute) != 1 else matched_attribute[0]
                    out += [tuple([matched_attribute if " " not in matched_attribute else f"'{matched_attribute}'", m.help_text])]

        for m in out:
            yield m

    @ensure_config
    def template_completion(
        self,
        incomplete: str,
        args: list[str] = None,
    ) -> Iterator[tuple[str, str]]:
        match = self.get_template_identifier(
            incomplete,
            completion=True,
        )
        out = []
        if match:
            match = [m for m in match if m.name not in args]
            for m in sorted(match, key=lambda i: i.name):
                out += [tuple([m.name, m.help_text])]

        for m in out:
            yield m

    @ensure_config
    def dev_template_completion(
        self,
        incomplete: str,
        args: list[str] = None,
    ) -> Iterator[tuple[str, str]]:
        match = self.get_template_identifier(
            incomplete,
            completion=True,
        )
        match = match or []
        dev_match = self.get_dev_identifier(
            incomplete,
            completion=True,
        )

        # filter device matches by those that are in template groups
        group_type = [(m.group, m.type) for m in dev_match]
        template_dev_match = []
        for (group, dev_type), dev in zip(group_type, dev_match):
            if dev_type == "ap":
                if self.groups_by_name.get(group, {"wlan_tg": True})["wlan_tg"] is True:
                    template_dev_match += [dev]
            elif dev_type in ["cx", "sw"]:
                if self.groups_by_name.get(group, {"wired_tg": True})["wired_tg"] is True:
                    template_dev_match += [dev]

        match += template_dev_match or []
        out = []
        if match:
            for m in sorted(match, key=lambda i: i.name):
                out += [tuple([m.name, m.help_text])]

        for m in out:
            yield m

    @ensure_config
    def dev_gw_switch_completion(
        self,
        ctx: typer.Context,
        incomplete: str,
        args: list[str] = None,
    ) -> Iterator[tuple[str, str]]:
        # typer stopped providing args pulling from ctx.params
        if not args:  # pragma: no cover
            args = [arg for p in ctx.params.values() for arg in utils.listify(p)]

        match = self.get_dev_identifier(incomplete, dev_type=["gw", "switch"], completion=True)

        out = [] if not match else [c for c in [m.get_completion(incomplete, args=args) for m in sorted(match, key=lambda i: i.name)] if c is not None]

        for m in out:
            yield m

    @ensure_config
    def dev_gw_switch_site_completion(
        self,
        ctx: typer.Context,
        incomplete: str,
        args: list[str] = None,
    ) -> Iterator[tuple[str, str]]:
        # Prevents exception during completion when config missing or invalid
        if self.config.valid:
            yield from self.dev_gw_switch_completion(ctx, incomplete, args=args)
            yield from self.site_completion(ctx, incomplete, args=args)

    @ensure_config
    def remove_completion(
        self,
        ctx: typer.Context,
        incomplete: str,
        args: list[str],
    ) -> Iterator[tuple[str, str]]:
        if args[-1].lower() == "site":
            yield from self.site_completion(ctx, incomplete)
        else:
            out = []
            if len(args) > 1:
                if "site" not in args and "site".startswith(incomplete.lower()):
                    out += ("site", )

            if "site" not in args:
                out += [m for m in self.dev_completion(incomplete=incomplete, args=args)]

            for m in out:
                yield m

    async def format_raw_devices_for_cache(self, resp: Response):
        dev_types = {
            "aps": "ap",
            "gateways": "gw",
        }
        switch_types = {
            "AOS-S": "sw",
            "AOS-CX": "cx"
        }
        raw_data = {
            url.split("/")[-1]: [
                {
                    "type": dev_types.get(url.split("/")[-1], switch_types.get(inner.get("switch_type", "err"))),
                    "swack_id": inner.get("stack_id", inner.get("swarm_id")) or (inner.get("serial", "err") if "swarm_id" in inner and inner.get("firmware_version", "").startswith("10.") else None),
                    **inner
                } for inner in resp.raw[url].get(url.split("/")[-1], {})  # Failed responses will lack the inner key with the devices
            ] for url in resp.raw
        }

        return raw_data

    # FIXME handle no devices in Central yet exception 837 --> cleaner.py 498
    async def update_dev_db(
            self,
            data: list[dict[str, Any]] | dict[str, Any],
            *,
            action: DBAction = DBAction.UPSERT,
        ) -> bool:
        """Update Device Database (local cache).

        If data is provided it's asumed to be a partial update.  No devices will be removed from the cache unless remove=True.
        To simply add entries to the Database call _update_db directly

        Args:
            data (list[dict[str, Any]] | dict[str, Any]): Device data to update cache with.
                Existing devices are retained and updated with any changes from the new data provided.
            action (DBAction, optional): Action to perform on cache Table. Defaults to DBAction.UPSERT.

        Returns:
            bool: Returns bool indicating the # of records updated in cache matches the # of devices sent.
        """
        return await self._update_db(Device, data=data, action=action, column="serial")

    async def prep_filtered_devs_for_cache(self, raw_models: list[models.Device], dev_type: constants.GenericDeviceTypes | list[constants.GenericDeviceTypes] = None, site: str = None, group: str = None) -> list[dict]:
        new_by_serial = {d.serial: d.model_dump() for d in raw_models}
        filters = {
            "dev_type": dev_type,
            "site": site,
            "group": group
        }
        filter_msg = ", ".join([f"{k}: {v if k != 'dev_type' else utils.unlistify(v)}" for k, v in filters.items() if v])

        cache_type = []
        if dev_type:
            switch_types = ["cx", "sw"] if "switch" in dev_type else []
            cache_type = [*[t for t in dev_type if t != "switch"], *switch_types]

        def include_device(dev: dict) -> bool:
            criteria = []
            if cache_type:
                criteria += [dev["type"] in cache_type]
            if site:
                criteria += [dev["site"] == site]
            if group:
                criteria += [dev["group"] == group]

            if all(criteria):
                if dev["serial"] not in new_by_serial:
                    return False

            return True

        cache_devices = {cd["serial"]: cd for cd in self.devices if include_device(cd)}

        update_data = {**cache_devices, **new_by_serial}
        log.info(f"Data prepared for device cache update.  Filters: {filter_msg}. Add/update {len(new_by_serial)} devices.  Devices in cache: Now: {len(list(self.devices))}, After Update: {len(update_data)}.")

        return list(update_data.values())

    async def refresh_dev_db(
            self,
            dev_type: constants.GenericDeviceTypes | list[constants.GenericDeviceTypes] = None,  # TODO make consistent throughout using device_type in many places
            group: str = None,
            site: str = None,
            label: str = None,
            serial: str = None,
            mac: str = None,
            model: str = None,
            stack_id: str = None,
            swarm_id: str = None,
            cluster_id: str = None,
            public_ip_address: str = None,
            status: constants.DeviceStatus = None,
            show_resource_details: bool = True,
            calculate_client_count: bool = True,
            calculate_ssid_count: bool = False,
            fields: list = None,
            offset: int = 0,
            limit: int = 1000,  # max allowed 1000
        ) -> CombinedResponse:
        """Get all devices from Aruba Central, and refresh local cache.

        Args:
            dev_type (Literal['ap', 'gw', 'cx', 'sw', 'sdwan', 'switch'], optional): Device Types to Update. Defaults to None.
            group (str, optional): Filter by devices in a Group. Defaults to None.
            site (str, optional): Filter by devices in a Site. Defaults to None.
            label (str, optional): Filter by devices with a label assigned. Defaults to None.
            serial (str, optional): Filter by Serial. Defaults to None.
            mac (str, optional): Filter by mac. Defaults to None.
            model (str, optional): Filter by model. Defaults to None.
            stack_id (str, optional): Filter by stack id (switches). Defaults to None.
            swarm_id (str, optional): Filter by swarm id (APs). Defaults to None.
            cluster_id (str, optional): Filter by cluster id. Defaults to None.
            public_ip_address (str, optional): Filter by public ip. Defaults to None.
            status (constants.DeviceStatus, optional): Filter by status. Defaults to None.
            show_resource_details (bool, optional): Show device resource utilization details. Defaults to True.
            calculate_client_count (bool, optional): Calculate client count. Defaults to True.
            calculate_ssid_count (bool, optional): Calculate SSID count. Defaults to False.
            fields (list, optional): fields to return. Defaults to None.
            offset (int, optional): pagination offset. Defaults to 0.
            limit (int, optional): pagination limit max 1000. Defaults to 1000.

        Returns:
            CombinedResponse: CombinedResponse object.
        """
        dev_type = None if not dev_type or dev_type == "all" else utils.listify(dev_type)
        # API only allows one of the filters below, if more are provided we send call with one and filter in the cleaner
        filter_params = {}
        exclusive_filter_params = {
            "swarm_id": swarm_id, "label": label, "cluster_id": cluster_id, "site": site, "group": group,
        }
        if len({k: v for k, v in exclusive_filter_params.items() if v}) > 1:
            for k, v in exclusive_filter_params.items():
                if v:
                    filter_params = {k: v}
                    break

        filter_params = filter_params or exclusive_filter_params

        resp: list[Response] | CombinedResponse = await api.monitoring.get_all_devices(
            dev_types=dev_type,
            # group=group,
            # site=site,
            # label=label,
            serial=serial,
            mac=mac,
            model=model,
            stack_id=stack_id,
            # swarm_id=swarm_id,
            # cluster_id=cluster_id,
            **filter_params,
            public_ip_address=public_ip_address,
            status=status,
            show_resource_details=show_resource_details,
            calculate_client_count=calculate_client_count,
            calculate_ssid_count=calculate_ssid_count,
            fields=fields,
            offset=offset,
            limit=limit,
            cache=True,
        )
        if isinstance(resp, CombinedResponse) and resp.ok:  # Can be Response | list[Response] if get_all_devices aborted due to failures
            # Any filters not in list below do not result in a cache update
            filtered_resonse = True if any([serial, mac, model, stack_id, public_ip_address, status, swarm_id, label, cluster_id]) else False
            raw_data = await self.format_raw_devices_for_cache(resp)
            with econsole.status(f"preparing {len(resp)} records for cache update"):
                _start_time = time.perf_counter()
                raw_models_by_type = models.Devices(**raw_data)
                raw_models = [*raw_models_by_type.aps, *raw_models_by_type.switches, *raw_models_by_type.gateways]
                update_data = [dev.model_dump() for dev in raw_models]
                log.debug(f"prepared {len(resp)} records for dev cache update in {round(time.perf_counter() - _start_time, 2)}")

            action = DBAction.UPSERT
            if resp.all_ok and not filtered_resonse:
                self.responses.dev = resp
                if dev_type or site:
                    if dev_type:
                        self.responses.device_type = dev_type
                        self.responses.device_kwargs["dev_type"] = dev_type
                    if site:
                        self.responses.device_kwargs["site"] = site
                else:  # request was for all devices with no filters we do a full refresh of dev cache
                    action = DBAction.REPLACE

            _ = await self._update_db(Device, data=update_data, action=action)

        return resp

    async def refresh_sub_db(self, sub_type: str = None, dev_type: str = None) -> Response:
        """Refresh Subscriptions Database (local cache).

        Returns:
            Response: CentralAPI Response object
        """
        glp_api = api_clients.glp
        if not glp_api:  # We only started caching subscription data with glp addition, classic does not cache subscriptions
            return await api.platform.get_subscriptions(sub_type=sub_type, device_type=dev_type)  # pragma: no cover

        resp = await glp_api.subscriptions.get_subscriptions(sub_type=sub_type, dev_type=dev_type)
        if resp.ok:
            self.responses.sub = resp
            sub_data = cnx_models.Subscriptions(**resp.raw)
            resp.output = sub_data.output()
            resp.caption = sub_data.counts
            if not any([sub_type, dev_type]):
                cache_data = sub_data.cache_dump()
            else:
                cache_data = list({**self.subscriptions_by_id, **{sub["id"]: sub for sub in sub_data.cache_dump()}}.values())

            _ = asyncio.create_task(self._update_db(Subscription, data=cache_data, action=DBAction.REPLACE))

        return resp

    async def update_floor_plan_cache(self, data, cache: Literal["buildings", "floors"] = "buildings") -> bool:
        if cache == "floors":
            model = models.Floors
            db = FloorPlanAP
        elif cache == "buildings":
            model = models.BuildingResponses
            db = Building

        try:
            data = model(data)
        except ValidationError as e:  # pragma: no cover
            log.error(utils.clean_validation_errors(e), show=True, caption=True, log=True)
            return False

        _ = asyncio.create_task(self._update_db(db, data=data.cache_dump(), action=DBAction.REPLACE))
        return True

    async def update_inv_db(
            self,
            data: list[dict[str, Any]] | dict[str, Any],
            *,
            action: DBAction = DBAction.UPSERT,
        ) -> bool:
        """Update Inventory Database (local cache).

        Args:
            data (list[dict[str, Any]] | dict[str, Any] | list[int] | int,): Data to be updated in Inventory, Existing inventory
                data is retained, new data is added, any changes in existing device is updated.
            action (DBAction, optional): Action to perform on cache Table. Defaults to DBAction.UPSERT.

        Returns:
            bool: Returns bool indicating the # of records updated in cache matches the # of devices sent.
        """
        cache_data = data if action == DBAction.DELETE else models.Inventory(utils.listify(data)).cache_dump()
        return await self._update_db(InventoryDevice, data=cache_data, action=action, column="serial")

    async def refresh_inv_db(
            self,
            dev_type: Literal['ap', 'gw', 'switch', 'bridge', 'all'] = None,
            serial_numbers: str | list[str] | tuple[str] | None = None,
            assigned: bool = None,
            archived: bool = None,
    ) -> Response:
        """Get devices from device inventory, and Update device Cache with results.

        Uses GLP API if configed, classic Central API if not.

        Args:
            dev_type (Literal['ap', 'gw', 'switch', 'all'], optional): Device Type.
                Defaults to None = 'all' device types.
            assigned (bool, optional): filter by devices that are assigned/lack assignment to a service (Aruba Central).
                Defaults to None: No filter by assignment.
            archived (bool, optional): filter by devices that are archived/unarchived (GLP Only).
                Defaults to None: All devices

        Returns:
            Response: CentralAPI Response object
        """
        if self.config.glp.ok:
            return await self.refresh_inv_db_glp(dev_type=dev_type, serial_numbers=serial_numbers, assigned=assigned, archived=archived)

        if archived is not None:
            raise ValueError("archived argument is only valid for GLP API, not classic")
        return await self.refresh_inv_db_classic(dev_type=dev_type)  # pragma: no cover

    async def refresh_inv_db_glp(
            self,
            dev_type: Literal['ap', 'gw', 'switch', 'bridge', 'all'] = None,  # dev_type is filtered after the API call for glp/cnx
            serial_numbers: str | list[str] | tuple[str] | None = None,
            assigned: bool = None,  # classic endpoint only returns assigned, this only applies to GLP
            archived: bool = None,
    ) -> Response:
        """Get devices from device inventory, and Update device Cache with results.

        This combines the results from 2 API calls:
            - classic.api.monitoring.get_device_inventory: /devices/<api version>/devices
            - classic.api.monitoring.get_subscriptions: /devices/<api version>/subscriptions

        Args:
            dev_type (Literal['ap', 'gw', 'switch', 'all'], optional): Device Type.
                Defaults to None = 'all' device types.
            serial_numbers: (str | list[str] | tuple[str], optional): For more effecient cache update.  Send all suspected serial numbers and on first failure an inv update
                will occur just for those serials.  Note: If any of the items sent do not appear to be serials, they are ignored.
            assigned (bool, optional): filter by devices that are assigned/lack assignment to a service (Aruba Central).
                Applies to GLP only.  Defaults to None: No filter by assignment.
            archived (bool, optional): filter by devices that are archived/unarchived.
                Defaults to None: All devices

        Returns:
            Response: CentralAPI Response object
        """
        br = BatchRequest
        glp_api = api_clients.glp

        # determine if all values provided are serial numbers if they are not we need to do a full inventory cache update
        _serial_numbers = None
        if serial_numbers:
            _serial_numbers = tuple([s for s in utils.listify(serial_numbers) if utils.is_serial(s)])
            if len(serial_numbers) != len(_serial_numbers):
                not_serials = [s for s in serial_numbers if s not in _serial_numbers]
                word = "None" if not _serial_numbers else len(not_serials)
                log.info(f"{word} of the {len(serial_numbers)} serial_numbers provided to cache.refresh_inv_db_glp do not appear to be serial numbers.", caption=True, log=True)
                log.debug(f"{not_serials = }")
                log.info(f"A Full Inventory cache update will occur disregarding {len(serial_numbers)} provided serial numbers.", caption=True, log=True)
                _serial_numbers = None

        batch_resp = await glp_api.session._batch_request(
            [
                br(glp_api.devices.get_devices, serial_numbers=_serial_numbers, assigned=assigned, archived=archived),
                br(glp_api.subscriptions.get_subscriptions),
            ]
        )

        if not any([r.ok for r in batch_resp]):
            log.error("Unable to perform Inv cache update due to API call failure", show=True)
            return batch_resp[0]  # will abort in _batch_request if first call fails.  Calling fucs expect a resp not [Response]

        inv_resp, sub_resp = batch_resp  # if first call failed above it doesn't get this far.

        inv_data, sub_data = None, None
        if not sub_resp.ok:
            log.error(f"Call to fetch subscription details failed.  {sub_resp.error}.  Subscription details provided from previously cached values.", caption=True)
            inv_data = cnx_models.Inventory(**inv_resp.raw)
            _inv_by_ser = {} if not inv_resp.ok else {dev["serialNumber"]: dev for dev in inv_resp.raw["items"]}
            combined = {serial: {**_inv_by_ser[serial], **self.inventory_by_serial.get(serial, {})} for serial in _inv_by_ser.keys()}
            inv_model = models.Inventory(list(combined.values()))
        else:
            with render.Spinner("Preparing inventory data for cache update", spinner="runner"):
                sub_data = cnx_models.Subscriptions(**sub_resp.raw)
                inv_data = cnx_models.Inventory(**inv_resp.raw)
                combined = await get_inventory_with_sub_data(inv_data, sub_data)
                inv_model = models.Inventory(combined)

        if dev_type and dev_type != "all":  # prepare data for cache
            dev_type: list[str] = [dev_type] if dev_type != "switch" else ["cx", "sw"]
            inv_model = models.Inventory([i for i in inv_model.model_dump() if i["type"] in dev_type])

        resp = [r for r in batch_resp if r.ok][-1]
        resp.rl = sorted([r.rl for r in batch_resp])[0]
        resp.raw = {r.url.path: r.raw for r in batch_resp}

        resp.output = inv_model.model_dump()
        if inv_data is not None:
            resp.caption = inv_data.counts

        # -- CACHE UPDATES --
        if archived is None:
            self.responses.inv = resp
            self.responses.device_type = dev_type
            self.responses.serial_numbers = serial_numbers

        if (dev_type is None or dev_type == "all") and not archived and not serial_numbers:
            _ = await self._update_db(InventoryDevice, data=inv_model.cache_dump(), action=DBAction.REPLACE)
        else:
            _ = await self._update_db(InventoryDevice, data=inv_model.cache_dump(), action=DBAction.UPSERT)

        if sub_data:
            self.responses.sub = sub_resp
            _ = asyncio.create_task(self._update_db(Subscription, data=sub_data.cache_dump(), action=DBAction.REPLACE))

        return resp

    # TODO need to make device_type consistent refresh_dev_db uses dev_type.  All CentralAPI methods use device_type
    async def refresh_inv_db_classic(
            self,
            dev_type: Literal['ap', 'gw', 'switch', 'all'] = None,
    ) -> Response:  # pragma: no cover
        """Get devices from device inventory, and Update device Cache with results.

        This combines the results from 2 API calls:
            - classic.api.monitoring.get_device_inventory: /platform/device_inventory/v1/devices
            - classic.api.monitoring.get_subscriptions: /platform/licensing/v1/subscriptions

        Args:
            device_type (Literal['ap', 'gw', 'switch', 'all'], optional): Device Type.
                Defaults to None = 'all' device types.

        Returns:
            Response: CentralAPI Response object
        """
        br = BatchRequest
        batch_resp = await api.session._batch_request(
            [
                br(api.platform.get_device_inventory, device_type=dev_type),
                br(api.platform.get_subscriptions, device_type=dev_type)
            ]
        )
        if not any([r.ok for r in batch_resp]):
            log.error("Unable to perform Inv cache update due to API call failure", show=True)
            return batch_resp

        inv_resp, sub_resp = batch_resp  # if first call failed above if would result in return.
        _inv_by_ser = {} if not inv_resp.ok else {dev["serial"]: dev for dev in inv_resp.raw["devices"]}

        if not sub_resp.ok:
            log.error(f"Call to fetch subscription details failed.  {sub_resp.error}.  Subscription details provided from previously cached values.", caption=True)
            combined = {serial: {**_inv_by_ser[serial], **self.inventory_by_serial.get(serial, {})} for serial in _inv_by_ser.keys()}
        else:
            raw_devs_by_serial = {serial: dev_data["subscription_key"] for serial, dev_data in _inv_by_ser.items()}
            dev_subs = list(set(raw_devs_by_serial.values()))
            subs_by_key = {sub["subscription_key"]: {"expires_in": sub["end_date"], "expired": sub["status"] == "EXPIRED"} for sub in sub_resp.output if sub["subscription_key"] in dev_subs}
            combined = {
                serial: {
                    **dev_data,
                    "subscription_expires": None if raw_devs_by_serial[serial] is None else subs_by_key[raw_devs_by_serial[serial]]["expires_in"]
                } for serial, dev_data in _inv_by_ser.items()
            }
        resp = [r for r in batch_resp if r.ok][-1]
        resp.rl = sorted([r.rl for r in batch_resp])[0]
        resp.raw = {r.url.path: r.raw for r in batch_resp}
        inv_model = models.Inventory(list(combined.values()))
        resp.output = inv_model.model_dump()
        resp.caption = inv_model.counts

        self.responses.inv = resp
        self.responses.device_type = dev_type
        action = DBAction.REPLACE if dev_type is None or dev_type == "all" else DBAction.UPSERT
        _ = await self._update_db(InventoryDevice, data=inv_model.cache_dump(), action=action)

        return resp

    async def update_site_db(self, data: SiteData = None, action: DBAction = DBAction.UPSERT) -> bool | None:
        update_data = data if action == DBAction.DELETE else models.Sites(utils.listify(data)).cache_dump()
        return await self._update_db(Site, data=update_data, action=action, column="name")

    async def refresh_site_db(self, force: bool = False) -> Response:
        if self.responses.site and not force:
            log.warning("cache.refresh_site_db called, but site cache has already been fetched this session.  Returning stored response.")
            return self.responses.site

        resp = await api.central.get_all_sites()
        if resp.ok:
            self.responses.site = resp
            if resp.output:
                sites = models.Sites(resp.raw["sites"])
                resp.output = sites.model_dump()
                _ = await self._update_db(Site, data=resp.output, action=DBAction.REPLACE)

        return resp

    async def update_group_db(self, data: list | dict, action: DBAction = DBAction.UPSERT) -> bool:
        return await self._update_db(Group, data=data, action=action, column="name")

    async def refresh_group_db(self) -> Response:
        if self.responses.group:  # pragma: no cover
            log.info("Update Group DB already refreshed in this session, returning previous group response")
            return self.responses.group

        resp = await api.configuration.get_all_groups()
        if resp.ok:
            self.responses.group = resp
            if resp.output:
                groups = models.Groups(resp.output)
                resp.output = groups.model_dump()

                _ = await self._update_db(Group, data=groups.cache_dump(), action=DBAction.REPLACE)

        return resp

    async def update_label_db(self, data: list[dict[str, Any]] | dict[str, Any] | list[int], action: DBAction = DBAction.UPSERT) -> Response:
        all_keys = utils.all_keys(list(data))
        column = "id" if "id" in all_keys else "name"
        cache_data = models.Labels(utils.listify(data))
        return await self._update_db(Label, data=cache_data.model_dump(), action=action, column=column)

    async def refresh_label_db(self) -> Response:
        resp: Response = await api.central.get_labels()
        if resp.ok:
            self.responses.label = resp
            if resp.output:  # cache update
                label_models = models.Labels(resp.output)
                _ = await self._update_db(Label, data=label_models.model_dump(), action=DBAction.REPLACE)
        return resp

    async def refresh_license_db(self) -> Response:  # TOGLP
        """Update License DB

        License DB stores the valid license names accepted by GreenLake/Central

        Returns:
            Response: CentralAPI Response Object
        """
        resp = await api.platform.get_valid_subscription_names()
        if resp.ok:
            resp.output = [{"name": k} for k in resp.output.keys() if self.is_central_license(k)]
            self.responses.license = resp
            _ = await self._update_db(SubscriptionName, data=resp.output, action=DBAction.REPLACE)
        return resp

    async def refresh_svc_db(self) -> Response:
        """Update Service DB (Aruba Central Application IDs from service catalog)

        Svc DB stores the Application IDs for Aruba Central based on what is
        provisioned in the workspace.

        Returns:
            Response: CentralAPI Response Object
        """
        resp = await api_clients.glp.service_managers.get_my_services()
        if resp.ok:
            self.responses.service = resp
            cache_data = [
                {
                    "name": "internal" if svc["serviceOffer"]["name"].lower().endswith("internal") else "public",
                    "id": svc["serviceManagerProvision"]["serviceManager"]["id"],
                    "region": svc["serviceManagerProvision"]["region"]
                } for svc in resp.output[0]["provisions"] if "networking central" in svc["serviceOffer"]["name"].lower()
            ]
            _ = await self._update_db(GLPService, data=cache_data, action=DBAction.REPLACE)
        return resp

    async def refresh_template_db(self) -> Response:
        if self.responses.template is not None:  # pragma: no cover
            log.warning("cache.refresh_template_db called, but template cache has already been fetched this session.  Returning stored response.")
            return self.responses.template

        if self.responses.group is None:
            gr_resp = await self.refresh_group_db()
            if not gr_resp.ok:
                return gr_resp

        groups = self.groups

        resp = await api.configuration.get_all_templates(groups=groups)
        if resp.ok:
            self.responses.template = resp
            if len(resp) > 0:  # handles initial cache population when none of the groups are template groups
                resp.output = utils.listify(resp.output)
                template_models = models.Templates(resp.output)
                resp.output = template_models.model_dump()
                _ = await self._update_db(Template, data=resp.output, action=DBAction.REPLACE)
        return resp

    async def update_template_db(self, data: list[dict[str, Any]] | dict[str, Any] = None, action: DBAction = DBAction.REPLACE) -> bool | None:
        return await self._update_db(Template, data=data, action=action, column=("name", "group"))

    async def refresh_client_db(
        self,
        client_type: constants.ClientType = None,
        group: str = None,
        swarm_id: str = None,
        label: str = None,
        network: str = None,
        site: str = None,
        serial: str = None,
        os_type: str = None,
        stack_id: str = None,
        cluster_id: str = None,
        band: str = None,
        mac: str = None,
        client_status: constants.ClientStatus = "CONNECTED",
        past: str = "3H",
    ) -> Response:
        """refresh client DB

        all args are passed to api.monitoring.get_clients, Local Cache is updated with any results.
        Local Cache retains clients connected within last 90 days by default.  Configuratble via cache_client_days
        in the config.

        It returns the raw data from the API with whatever filters were provided by the user
        then updates the db with the data returned

        Args:
            client_type (Literal['wired', 'wireless', 'all'], optional): Client type to retrieve.  Defaults to None.
                if not provided all client types will be returned, unless a filter specific to a client type is
                specified.  i.e. providing band will result in WLAN clients.
            group (str, optional): Filter by Group. Defaults to None.
            swarm_id (str, optional): Filter by swarm. Defaults to None.
            label (str, optional): Filter by label. Defaults to None.
            network (str, optional): Filter by WLAN SSID. Defaults to None.
            site (str, optional): Filter by site. Defaults to None.
            serial (str, optional): Filter by connected device serial. Defaults to None.
            os_type (str, optional): Filter by client OS type. Defaults to None.
            stack_id (str, optional): Filter by Stack ID. Defaults to None.
            cluster_id (str, optional): Filter by Cluster ID. Defaults to None.
            band (str, optional): Filter by band. Defaults to None.
            mac (str, optional): Filter by client MAC. Defaults to None.
            client_status (Literal["FAILED_TO_CONNECT", "CONNECTED"], optional): Return clients that are
                connected, or clients that have failed to connect.  Defaults to CONNECTED.
            past: (str, optional): Time-range to show client details for.  Format:
                3H = 3 Hours, 1D = 1 Day, 1W = 1 Week, 1M = 1Month, 3M = 3Months.  Defaults to 3H

        Past users are always retained, unless truncate=True
        """
        resp: Response = await api.monitoring.get_clients(
            client_type=client_type,
            group=group,
            swarm_id=swarm_id,
            label=label,
            network=network,
            site=site,
            serial=serial,
            os_type=os_type,
            stack_id=stack_id,
            cluster_id=cluster_id,
            band=band,
            mac=mac,
            client_status=client_status,
            past=past,
        )
        if not resp.ok or not len(resp) > 0:
            return resp

        resp.output = utils.listify(resp.output)
        with econsole.status(f"Preparing [cyan]{len(resp.output)}[/] clients for cache update"):
            new_clients = models.Clients(resp.output)  # TODO we can use model_dump to update resp.output negating need for the cleaner
            if "wireless" in [new_clients[0].type, new_clients[-1].type]:
                self.responses.client = resp
        _ = await self._update_db(Client, data=new_clients.cache_dump(), action=DBAction.UPSERT)

        return resp

    def update_central_audit_log_db(self, log_data: list[dict[str, Any]]) -> bool:
        return asyncio.run(self._update_db(CentralAuditLog, data=log_data, action=DBAction.REPLACE))

    def update_event_db(self, log_data: list[dict[str, Any]]) -> bool:
        return asyncio.run(self._update_db(Event, data=log_data, action=DBAction.REPLACE))

    async def update_hook_data_db(self, data: list[dict[str, Any]]) -> bool:  # pragma: no cover  ... used by hook proxy
        data = utils.listify(data)
        rem_data = []
        add_data = []
        for d in data:
            if d.get("state", "") == "Close":
                rem_data += [d]
            else:
                add_data += [d]

        if rem_data and add_data:
            log.error("update_hook_data_db called with both open and closed notifications")

        if rem_data:
            log.info(f"Removing {rem_data} from HookDataDB")
            return await self._update_db(WebHookData, data=rem_data, action=DBAction.DELETE, column="id")
        else:
            data = [*self.hook_active, *(add_data or data)]
            return await self._update_db(WebHookData, data=data, action=DBAction.REPLACE)

    # Not tested or used yet, until we have commands that add/del MPSK networks
    async def update_mpsk_net_db(self, data: list[dict[str, Any]], action: DBAction = DBAction.REPLACE) -> bool:  # pragma: no cover
        _data = models.MpskNetworks(utils.listify(data))
        return await self._update_db(MPSKNetwork, data=_data.model_dump(), action=action, column="id")

    async def refresh_mpsk_networks_db(self) -> Response:
        resp = await api.cloudauth.get_mpsk_networks()
        if resp.ok:
            self.responses.mpsk = resp
            if resp.output:
                _update_data = models.MpskNetworks(resp.raw)
                _ = await self._update_db(MPSKNetwork, data=_update_data.model_dump(), action=DBAction.REPLACE)

        return resp

    async def refresh_mpsk_db(self, mpsk_id: str = None, name: str = None, role: str = None, status: MPSKStatus = None) -> Response:
        if not mpsk_id:
            net_resp = await self.refresh_mpsk_networks_db()
            if not net_resp.ok:
                log.error("Unable to refresh named mpsks as call to fetch mpsk networks failed", caption=True)
                return net_resp
            if not net_resp.output:
                log.info("Unable to refresh named mpsks as No MPSK networks are configured", caption=True)
                return net_resp

            mpsk_networks = {net["id"]: net["ssid"] for net in net_resp.output}
            named_reqs = [
                BatchRequest(api.cloudauth.get_named_mpsk, mpsk_id, name=name, role=role, status=status)
                for mpsk_id in mpsk_networks
            ]
            batch_resp = await api.session._batch_request(named_reqs)  # TODO can use BatchResponse for this now

            passed: list[Response] = []
            failed: list[Response] = []
            for resp, network in zip(batch_resp, mpsk_networks.values()):
                if resp.ok:
                    passed += [resp]
                    resp.output = [
                        {"ssid": network, **inner}
                        for inner in resp.output
                    ]
                else:
                    failed += [resp]
                    log.error(f"Skipping cache update for MPSKs associated with {network} due to failure {resp.error}", show=True)

            if not passed:
                return failed[-1]
            resp = passed[-1]
            resp.rl = min([r.rl for r in batch_resp])
            resp.output = [inner for r in passed for inner in r.output]
        else:
            resp = await api.cloudauth.get_named_mpsk(mpsk_id, name=name, role=role, status=status)
            if resp.ok:
                ssid: CacheMpskNetwork = self.get_mpsk_network_identifier(mpsk_id, silent=True)
                if ssid:
                    resp.output = [{"ssid": ssid.name, **inner} for inner in resp.output]

        # cache update
        if resp.ok:
            self.responses.mpsk = resp
            if resp.output:  # necessary in case there are no named mpsks defined
                _update_data = models.Mpsks(resp.output)

                action = DBAction.REPLACE if not mpsk_id and not any([name, role, status]) else DBAction.UPSERT
                _ = await self._update_db(MPSK, data=_update_data.model_dump(), action=action)

        return resp

    async def update_portal_db(self, data: list[dict[str, Any]] | list[int], action: DBAction = DBAction.UPSERT) -> bool:
        update_data = data if action == DBAction.DELETE else models.Portals(utils.listify(data)).model_dump()
        return await self._update_db(Portal, data=update_data, action=action, column="id")

    async def refresh_portal_db(self) -> Response:
        resp = await api.guest.get_portals()
        if not resp.ok:
            return resp

        self.responses.portal = resp
        if resp.output:
            self.responses.portal = resp
            portal_model = models.Portals(deepcopy(resp.output))
            _ = await self._update_db(Portal, data=portal_model.model_dump(), action=DBAction.REPLACE)

        return resp

    async def update_cert_db(self, data: list[dict[str, Any]] | list[int], action: DBAction = DBAction.UPSERT) -> bool:
        update_data = data if action == DBAction.DELETE else models.Certs(utils.listify(data)).model_dump()
        return await self._update_db(Cert, data=update_data, action=action, column="name")

    async def refresh_cert_db(self, *, query: str = None) -> Response:
        resp: Response = await api.configuration.get_certificates(query)
        if not resp.ok:
            return resp

        self.responses.cert = resp
        if resp.output:
            action = DBAction.REPLACE if not query else DBAction.UPSERT
            cert_models = models.Certs(resp.output)
            _ = await self._update_db(Cert, data=cert_models.model_dump(), action=action, column="name")

        return resp

    async def update_guest_db(self, data: list[dict[str, Any]] | dict[str, Any], portal_id: str = None, action: DBAction = DBAction.UPSERT) -> bool:
        # no cover: start
        update_data = data if action == DBAction.DELETE else models.Guests(portal_id, utils.listify(data)).model_dump()
        return await self._update_db(Guest, data=update_data, action=action, column="id")
        # no cover: stop  add guest uses update_db directly, this would come into play if we add batch add guests

    async def refresh_guest_db(self, portal_id: str) -> Response:
        resp: Response = await api.guest.get_guests(portal_id)
        if not resp.ok:
            return resp

        self.responses.guest = resp
        if resp.output:
            guest_models = models.Guests(portal_id, deepcopy(resp.output))
            _ = await self._update_db(Guest, data=guest_models.model_dump(), action=DBAction.UPSERT)  # <-- UPSERT as this seems to be specific to a portal and there could be multiple portals.

        return resp

    # TODO cache.groups cache.devices etc change to Response object with data in output.  So they can be leveraged in commands with all attributes
    async def _check_fresh(
        self,
        dev_db: bool = False,
        inv_db: bool = False,
        site_db: bool = False,
        template_db: bool = False,
        group_db: bool = False,
        label_db: bool = False,
        license_db: bool = False,
        app_db: bool = False,
        dev_type: constants.AllDevTypes = None,
        assigned: bool = None,
        archived: bool = None,
        serial_numbers: str | list[str] | tuple[str] | None = None,
        ):
        update_funcs = []
        db_res: CombinedResponse | list[Response] = []
        dev_update_funcs = ["refresh_inv_db", "refresh_dev_db"]
        if group_db:
            update_funcs += [self.refresh_group_db]
        if dev_db:
            update_funcs += [self.refresh_dev_db]
        if inv_db:
            update_funcs += [self.refresh_inv_db]
        if site_db:
            update_funcs += [self.refresh_site_db]
        if template_db:
            update_funcs += [self.refresh_template_db]
        if label_db:
            update_funcs += [self.refresh_label_db]
        if license_db:
            update_funcs += [self.refresh_license_db]
        if app_db and self.config.glp.ok:
            update_funcs += [self.refresh_svc_db]  # app db only updated when full refresh is done as the app ids should not change
        inv_update_kwargs = {} if not self.config.glp.ok or not serial_numbers else {"serial_numbers": serial_numbers, "assigned": assigned, "archived": archived}

        if update_funcs:
            kwarg_list = [{} if f.__name__ not in dev_update_funcs else {"dev_type": dev_type} if f.__name__ != "refresh_inv_db" else {"dev_type": dev_type, **inv_update_kwargs} for f in update_funcs]
            db_res += [await update_funcs[0](**kwarg_list[0])]
            if isinstance(db_res[0], list):  # needed as refresh_dev_db (if no dev_types provided) may return a CombinedResponse, but can also return a list of Responses if all failed meaning the above creates a list[list]
                db_res = utils.unlistify(db_res)

            if not db_res[-1]:
                _remaining = 0 if len(update_funcs) == 1 else len(update_funcs[1:])
                if _remaining:
                    log.error(f"Cache Update aborting remaining {len(update_funcs)} cache updates due to failure in {update_funcs[0].__name__}", show=True, caption=True)
                    db_res += [Response(error=f"{f.__name__} aborted due to failure in previous cache update call ({update_funcs[0].__name__})") for f in update_funcs[1:]]
                else:
                    log.error(f"Cache Update failure in {update_funcs[0].__name__}: {db_res[0].error}", show=True, caption=True)

            else:
                if len(update_funcs) > 1:
                    db_res = [*db_res, *await asyncio.gather(*[f(**k) for f, k in zip(update_funcs[1:], kwarg_list[1:])])]

        # If all *_db params are false refresh cache for all
        # TODO make more elegant
        else:  # TODO asyncio.sleep is a temp until build better session wide rate limit handling.
            br = BatchRequest
            db_res += await api.session._batch_request([br(self.refresh_group_db), br(asyncio.sleep, .5)])  # update groups first so template update can use the result group_update is 3 calls.
            if db_res[-1]:
                dev_res = await api.session._batch_request([br(self.refresh_dev_db), br(asyncio.sleep, .5)])   # dev_db separate as it is a multi-call 3 API calls.
                dev_res = utils.unlistify(dev_res)  # should only be an issue when debugging (re-writing responses) in refresh_dev_db
                if isinstance(dev_res, list):
                    db_res = [*db_res, *dev_res]
                else:
                    db_res += [dev_res]
                remaining_cache_updates = [self.refresh_inv_db, self.refresh_site_db, self.refresh_template_db, self.refresh_label_db, self.refresh_license_db]
                if self.config.glp.ok:
                    remaining_cache_updates += [self.refresh_svc_db]
                if db_res[-1]:
                    batch_reqs = [BatchRequest(req) for req in remaining_cache_updates]
                    db_res = [*db_res, *await api.session._batch_request(batch_reqs)]

        return db_res

    def check_fresh(
        self,
        *,
        refresh: bool = False,
        site_db: bool = False,
        dev_db: bool = False,
        inv_db: bool = False,
        template_db: bool = False,
        group_db: bool = False,
        label_db: bool = False,
        license_db: bool = False,
        app_db: bool = False,
        dev_type: constants.GenericDeviceTypes = None,
        assigned: bool = None,
        archived: bool = None,
        serial_numbers: str | list[str] | tuple[str] | None = None,
    ) -> list[Response]:
        db_res = None
        db_map = {
            "group_db": group_db,
            "dev_db": dev_db,
            "inv_db": inv_db,
            "site_db": site_db,
            "template_db": template_db,
            "label_db": label_db,
            "license_db": license_db,
            "app_db": app_db,
        }
        update_count = list(db_map.values()).count(True)
        update_count += 0 if not inv_db else 1  # inv_db includes update for sub_db
        refresh = refresh or bool(update_count)  # if any DBs are set to update they will update regardless of refresh value
        update_all = True if not update_count else False  # if all are False default is to update all DBs but only if refresh=True

        if refresh or not self.config.cache.ok:
            _word = "Refreshing" if self.config.cache.ok else "Populating"
            updating_db = "[bright_green]Full[/] Identifier mapping" if not update_count else utils.color([k for k, v in db_map.items() if v])
            econsole.print(f"[cyan]-- {_word} {updating_db} cache --[/cyan]", end="")

            start = time.perf_counter()
            db_res = asyncio.run(self._check_fresh(**db_map, dev_type=dev_type, assigned=assigned, archived=archived, serial_numbers=serial_numbers))
            elapsed = round(time.perf_counter() - start, 2)
            failed = [r for r in db_res if not r.ok]
            log.info(f"Cache Refreshed {update_count if update_count != len(db_map) else 'all'} table{'s' if update_count > 1 else ''} in {elapsed}s")

            if failed:
                try:
                    res_map = ", ".join(db for idx, (db, do_update) in enumerate(db_map.items()) if do_update or update_all and not db_res[idx].ok)
                    err_msg = f"Cache refresh returned an error updating {res_map}"  # TODO this logic gets screwy because if dev_db all calls fail the return is list[Response] with len 3 rather than  CombinedResponse
                except IndexError:
                    err_msg = f"Cache refresh returned an error. {len(failed)} requests failed."
                log.error(err_msg)
                api.session.spinner.fail(err_msg)
            else:
                api.session.spinner.succeed(f"Cache Refresh [bright_green]Completed[/] in [cyan]{elapsed}[/]s")

        return db_res

    def handle_multi_match(
        self,
        match: list[CentralObject] | list[models.Client],
        query_str: str = None,
        query_type: str = "device",
    ) -> list[CacheObject]:  # pragma: no cover  required tty, not part of automated testing
        if env.is_pytest:
            log.error(f"handle_multi_match called from pytest run during test: {env.current_test}.  Check fixtures/cache. {match =}", show=True)
            raise typer.Exit(91)

        typer.echo()
        field_map = {
            "site": {"name", "city", "state", "type"},
            "template": {"name", "group", "model", "device_type", "version"},
            "group": {"name"},
            "label": {"name"},
            "inventory": {"serial", "mac"},
            "client": {"name", "mac", "ip", "connected_port", "connected_name", "site"},
            "certificate": {"name", "type", "expired", "expiration", "md5_checksum"},
            "sub": {"name", "end_date", "expired", "available", "id"},
        }
        fields = field_map.get(query_type, {"name", "serial", "mac", "type"})
        set_width_cols = {} if query_type != "group" else {"name": {"min": 20, "max": None}}

        if isinstance(match[0], models.Client):
            data = [{k: d[k] for k in d.keys() if k in fields} for d in match]
        elif query_type == "sub":
            data = list(sorted([{k: v if k != "end_date" else DateTime(v, 'date-string') for k, v in d.items() if k in fields} for d in match], key=lambda x: (x["end_date"], x["available"]), reverse=True))
        else:
            data = [{k: d[k] for k in d.data if k in fields} for d in match]

        out = render.output(
            data,
            title=f"Ambiguous identifier. Select desired {query_type}.",
            set_width_cols=set_width_cols,
        )
        menu = out.menu(data_len=len(match))

        if query_str:
            menu = menu.replace(query_str, typer.style(query_str, fg="bright_cyan"))
            menu = menu.replace(query_str.upper(), typer.style(query_str.upper(), fg="bright_cyan"))
        typer.echo(menu)
        selection = ""
        valid = [str(idx + 1) for idx, _ in enumerate(match)]
        try:
            while selection not in valid:
                selection = typer.prompt(f"Select {query_type.title()}")
                if not selection or selection not in valid:
                    typer.secho(f"Invalid selection {selection}, try again.")
        except KeyboardInterrupt:
            raise typer.Abort()

        return [match[int(selection) - 1]]

    def get_identifier(
        self,
        qry_str: str,
        qry_funcs: Sequence[str],
        device_type: str | list[str] = None,
        swack: bool = False,
        swack_only: bool = False,
        group: str | list[str] = None,
        completion: bool = False,
    ) -> CentralObject | list[CentralObject]:
        """Get Identifier when iden type could be one of multiple types.  i.e. device or group

        Args:
            qry_str (str): The query string provided by user.
            qry_funcs (Sequence[str]): Sequence of strings "dev", "group", "site", "template"
            device_type (Union[str, list[str]], optional): Restrict matches to specific dev type(s).
                Defaults to None.
            swack (bool, optional): Similar to swack, but only filters member switches of stacks, but will also return any standalone switches that match.
                Does not filter non stacks, the way swack option does. Defaults to False.
            swack_only (bool, optional): Restrict matches to only the stack commanders matching query (filter member switches).
                Defaults to False.
            group (str, list[str], optional): applies to get_template_identifier, Only match if template is in provided group(s).
                Defaults to None.
            completion (bool, optional): If function is being called for AutoCompletion purposes. Defaults to False.
                When called for completion it will fail silently and will return multiple when multiple matches are found.

        Raises:
            typer.Exit: If not ran for completion, and there is no match, exit with code 1.

        Returns:
            CentralObject or list[CentralObject, ...]
        """
        device_type = utils.listify(device_type)
        default_kwargs = {"retry": False, "completion": completion, "silent": True}
        if "dev" in qry_funcs:  # move dev query last
            qry_funcs = [*[q for q in qry_funcs if q != "dev"], *["dev"]]

        match: list[CacheDevice | CacheGroup | CacheSite | CacheTemplate] = []
        for idx in range(0, 2):
            for q in qry_funcs:
                kwargs = default_kwargs.copy()
                if q == "dev":
                    kwargs["dev_type"] = device_type
                    kwargs["swack_only"] = swack_only
                    kwargs["swack"] = swack
                elif q == "template":
                    kwargs["group"] = group
                this_match = getattr(self, f"get_{q}_identifier")(qry_str, **kwargs) or []
                match = [*match, *[m for m in utils.listify(this_match) if m not in match]]

                if match and not completion:
                    # user selects which device if multiple matches returned
                    if len(match) > 1:
                        match = self.handle_multi_match(match, query_str=qry_str,)

                    return match[0]

            # No match found trigger refresh and try again.
            if idx == 0 and not match and not completion:
                self.check_fresh(
                    dev_db=True if "dev" in qry_funcs else False,
                    site_db=True if "site" in qry_funcs else False,
                    template_db=True if "template" in qry_funcs else False,
                    group_db=True if "group" in qry_funcs else False,
                )

        if completion:
            return match

        if not match:
            econsole.print(f"[dark_orange3]:warning:[/]  [bright_red]Unable to find a matching identifier[/] for [cyan]{qry_str}[/], tried: [cyan]{qry_funcs}[/]")
            raise typer.Exit(1)

    @overload
    def get_dev_identifier(
        self,
        query_str: str,
        dev_type: constants.LibAllDevTypes | list[constants.LibAllDevTypes] | None,
        include_inventory: bool,
    ) -> CacheDevice | CacheInvDevice: ...  # pragma: no cover

    @overload
    def get_dev_identifier(
        self,
        query_str: str,
        dev_type: constants.LibAllDevTypes | list[constants.LibAllDevTypes],
        swack: Literal[True],
    ) -> CacheDevice: ...  # pragma: no cover

    @overload
    def get_dev_identifier(
        self,
        query_str: str,
        dev_type: constants.LibAllDevTypes | list[constants.LibAllDevTypes],
        swack_only: Literal[True],
    ) -> CacheDevice: ...  # pragma: no cover

    @overload
    def get_dev_identifier(
        self,
        query_str: str,
        dev_type: constants.LibAllDevTypes,
        swack_only: Literal[True],
    ) -> CacheDevice: ...  # pragma: no cover

    @overload
    def get_dev_identifier(
        self,
        query_str: str | Iterable[str],
        dev_type: Optional[constants.LibAllDevTypes | list[constants.LibAllDevTypes]],
        swack: Optional[bool],
        swack_only: Optional[bool],
        retry: Optional[bool],
        completion: bool,
        silent: Optional[bool],
    ) -> list[CacheDevice]: ...  # pragma: no cover

    @overload
    def get_dev_identifier(
        self,
        query_str: str | Iterable[str],
        retry: Literal[False],
        silent: Literal[True],
        exit_on_fail: Literal[False],
    ) -> CacheDevice | None: ...  # pragma: no cover

    @overload
    def get_dev_identifier(
        self,
        query_str: str | Iterable[str],
        dev_type: list[constants.LibAllDevTypes],
        completion: Literal[True],
    ) -> list[CacheDevice]: ...  # pragma: no cover

    @overload
    def get_dev_identifier(
        self,
        query_str: str | Iterable[str],
        silent: bool,
        include_inventory: bool,
        exit_on_fail: Literal[False],
        retry: bool,
    ) -> CacheDevice | CacheInvDevice | None: ...  # pragma: no cover

    @overload  # include_inventory=True, swack=True, silent=True, exit_on_fail=False
    def get_dev_identifier(
        self,
        query_str: str | Iterable[str],
        include_inventory: Literal[True],
        swack: Literal[True],
        silent: bool,
        exit_on_fail: Literal[False]
    ) -> CacheDevice | CacheInvDevice | None: ...  # pragma: no cover

    @overload
    def get_dev_identifier(
        self,
        query_str: str | Iterable[str],
        completion: Literal[True],
    ) -> list[CacheDevice]: ...  # pragma: no cover

    @overload
    def get_dev_identifier(
        self,
        query_str: str | Iterable[str],
        dev_type: Optional[constants.LibAllDevTypes | list[constants.LibAllDevTypes] | None],
        swack: Optional[bool],
        completion: Literal[True],
    ) -> list[CacheDevice]: ...  # pragma: no cover

    @overload
    def get_dev_identifier(
        self,
        query_str: str | Iterable[str],
        dev_type: Optional[constants.LibAllDevTypes | list[constants.LibAllDevTypes] | None],
        swack: Optional[bool],
        swack_only: Optional[bool],
        retry: Optional[bool],
        completion: bool,
        silent: Optional[bool],
        exit_on_fail: Literal[False]
    ) -> list[CacheDevice | None]: ...  # pragma: no cover

    @overload
    def get_dev_identifier(
        query_str: str,
        completion: Literal[True]
    ) -> list[CacheDevice]: ...  # pragma: no cover

    @overload
    def get_dev_identifier(
        query_str: str,
        dev_type: Optional[constants.LibAllDevTypes | list[constants.LibAllDevTypes] | None],
        retry: bool,
        completion: bool,
        silent: bool,
        exit_on_fail: Literal[False]
    ) -> list[CacheDevice | None]: ...  # pragma: no cover

    @overload
    def get_dev_identifier(
        self,
        query_str: str | Iterable[str],
        dev_type: Optional[constants.LibAllDevTypes | list[constants.LibAllDevTypes]],
        swack: Optional[bool],
        swack_only: Optional[bool],
        retry: Optional[bool],
        completion: bool,
        silent: Optional[bool],
        include_inventory: bool,
        exit_on_fail: bool
    ) -> list[CacheDevice | CacheInvDevice | None]: ...  # pragma: no cover

    @overload
    def get_dev_identifier(
        self,
        query_str: str,
        dev_type: constants.LibAllDevTypes | list[constants.LibAllDevTypes],
        swack: bool,
    ) -> CacheDevice: ...  # pragma: no cover

    @overload
    def get_dev_identifier(
        self,
        query_str: str,
        dev_type: constants.LibAllDevTypes | list[constants.LibAllDevTypes],
    ) -> CacheDevice: ...  # pragma: no cover

    @overload
    def get_dev_identifier(
        self,
        query_str: str,
        swack: bool,
    ) -> CacheDevice: ...  # pragma: no cover

    @overload
    def get_dev_identifier(
        self,
        query_str: str,
        include_inventory: bool,
        swack: bool,
    ) -> CacheDevice: ...  # pragma: no cover

    @overload
    def get_dev_identifier(
        self,
        query_str: str,
    ) -> CacheDevice: ...  # pragma: no cover

    @overload
    def get_dev_identifier(
        self,
        query_str: str,
        silent: Literal[True],
        exit_on_fail: Literal[False]
    ) -> CacheDevice | None: ...  # pragma: no cover

    @overload
    def get_dev_identifier(
        self,
        query_str: str | Iterable[str],
        dev_type: Optional[constants.LibAllDevTypes | list[constants.LibAllDevTypes]],
        swack: Optional[bool],
        swack_only: Optional[bool],
        retry: Optional[bool],
        silent: Optional[bool],
    ) -> CacheDevice: ...  # pragma: no cover

    @overload
    def get_dev_identifier(
        self,
        query_str: str | Iterable[str],
        dev_type: Optional[constants.LibAllDevTypes | list[constants.LibAllDevTypes]],
        swack: Optional[bool],
        swack_only: Optional[bool],
        retry: Optional[bool],
        silent: Optional[bool],
        include_inventory: Literal[True],
    ) -> CacheDevice | CacheInvDevice: ...  # pragma: no cover

    @overload
    def get_dev_identifier(
        self,
        query_str: str | Iterable[str],
        dev_type: Optional[constants.LibAllDevTypes | list[constants.LibAllDevTypes]],
        swack: Optional[bool],
        swack_only: Optional[bool],
        retry: Optional[bool],
        silent: Optional[bool],
        include_inventory: Optional[bool] = False,
        exit_on_fail: bool = False,
    ) -> CacheDevice | CacheInvDevice | None: ...  # pragma: no cover

    def get_dev_identifier(
        self,
        query_str: str | Iterable[str],
        dev_type: Optional[constants.LibAllDevTypes | list[constants.LibAllDevTypes]] = None,
        swack: Optional[bool] = False,
        swack_only: Optional[bool] = False,
        retry: Optional[bool] = True,
        completion: Optional[bool] = False,
        silent: Optional[bool] = False,
        include_inventory: Optional[bool] = False,
        exit_on_fail: Optional[bool] = True,
    ) -> CacheDevice | CacheInvDevice | list[CacheDevice] | list[CacheDevice | CacheInvDevice] | list[CacheDevice | CacheInvDevice | None] | None:
        """Get Devices from local cache, starting with most exact match, and progressively getting less exact.

        If multiple matches are found user is promted to select device.

        Args:
            query_str (str | Iterable[str]): The query string or list of strings to attempt to match.
            dev_type (Literal["ap", "cx", "sw", "switch", "gw"] | list[Literal["ap", "cx", "sw", "switch", "gw"]], optional): Limit matches to specific device type. Defaults to None (all device types).
            swack (bool, optional): For switches only return the conductor switch that matches. For APs only return the VC of the swarm the match belongs to. Defaults to False.
                Does not filter non stacks.
            swack_only (bool, optional): For switches only return the conductor switch that matches. For APs only return the VC of the swarm the match belongs to. Defaults to False.
                If True devices that lack a swack_id (swarm_id | stack_id) are filtered (even if they match).
            retry (bool, optional): If failure to match should result in a cache update and retry. Defaults to True.
            completion (bool, optional): If this is being called for tab completion (Allows multiple matches, implies retry=False, silent=True, exit_on_fail=False). Defaults to False.
            silent (bool, optional): Do not display errors / output, simply returns match if match is found. Defaults to False.
            include_inventory (bool, optional): Whether match attempt should also include Inventory DB (devices in GLP that have yet to connect to Central). Defaults to False.
            exit_on_fail (bool, optional): Whether a failure to match exits the program. Defaults to True.

        Raises:
            typer.Exit: Exit CLI / command, occurs if there is no match unless exit_on_fail is set to False.

        Returns:
            CacheDevice | list[CacheDevice] | None: if completion = True returns list[CacheDevice] containing all matches or None if there was no match.
                Otherwise return will be the CacheDevice that matched.  (If completion=False and multiple matches are found, user is prompted to select)
        """
        retry = False if completion else retry
        cache_updated = False
        if dev_type:
            dev_type = utils.listify(dev_type)
            if "switch" in dev_type:
                dev_type = list(set(filter(lambda t: t != "switch", [*dev_type, "cx", "sw"])))

        if isinstance(query_str, (list, tuple)):
            query_str = " ".join(query_str)

        if not query_str and completion:
            if dev_type:
                return [dev for dev in self.devices if dev.type in dev_type]
            return list(self.devices)

        mac_exact = mac_fuzzy = ()
        if utils.Mac(query_str, fuzzy=True):
            mac_exact = (Device.mac == utils.Mac(query_str).cols.lower(),)
            mac_fuzzy = (Device.mac.istartswith(utils.Mac(query_str, fuzzy=completion).cols.lower()),)

        statements = [
            select(Device).where(or_(Device.name == query_str, Device.serial == query_str, *mac_exact, Device.ip == query_str.split("/")[0])),  # exact match  MAC is stored in DB as lowercase/cols delims
            select(Device).where(or_(func.lower(Device.name) == func.lower(query_str), func.lower(Device.serial) == func.lower(query_str))),  # case insensitive match
            select(Device).where(Device.name.like(query_str.replace("-", "_"))),  # _ is wildcard for like() ... match ignoring - and _
            select(Device).where(or_(Device.name.istartswith(query_str), Device.serial.istartswith(query_str), *mac_fuzzy, Device.ip.istartswith(query_str))),  # case insensitive startswith match
            select(Device).where(or_(Device.name.istartswith(query_str.replace("-", "_")), Device.serial.istartswith(query_str.replace("-", "_")))),  # case insensitive startswith ignore -_ match _ is wildcard for istartswith  <-- Query returns bogus results
        ]
        inv_statement = select(InventoryDevice).where(or_(InventoryDevice.serial == query_str, InventoryDevice.mac == utils.Mac(query_str).cols.lower()))

        matches = inv_matches = all_matches = []
        out: list[CacheDevice | CacheInvDevice] = []
        for _ in range(0, 2 if retry else 1):
            with Session(self.engine) as session:
                for idx, stmt in enumerate(statements):
                    matches = session.scalars(stmt).all()
                    if matches:
                        break
                    if idx == 0 and not matches and include_inventory:
                        inv_matches = session.scalars(inv_statement).all()

            if matches and dev_type:
                all_matches = matches.copy()
                matches = [d for d in matches if d.type in dev_type]

            # no match found initiate cache update
            if retry and not matches and self.responses.dev is None:
                if dev_type and (cache_updated or self.responses.device_type == dev_type):
                    ...  # pragma: no cover self.responses.dev is not currently updated if dev_type provided [ update it does now, but keeping this in until tested ], but cache update may have already occured in this session.
                else:
                    if not any([matches, inv_matches]):
                        _msg = f"[bright_red]No Match found[/] in {'Inventory or Device (monitoring)' if include_inventory else 'Device (monitoring)'} Cache"
                    else:
                        _msg = "[bright_red]No Match found[/]" if not inv_matches else "[bright_green]Match found in Inventory Cache[/], [bright_red]No Match found in Device (monitoring) Cache[/]"
                    dev_type_sfx = "" if not dev_type else f" [dim italic](Device Type: {utils.unlistify(dev_type)})[/]"
                    econsole.print(f"{emoji.warn} {_msg} for [cyan]{query_str}[/]{dev_type_sfx}.")

                    if FUZZ and self.devices and not silent:
                        matches = self.fuzz_lookup(query_str, table=Device, cache_object=CacheDevice, dev_type=dev_type)

                    # If there is an inventory only match we still update monitoring cache (to see if device came online since it was added. Otherwise commands like move will reject due to only being in Inventory)
                    if not matches:
                        kwargs = {"dev_db": True}
                        if include_inventory and not inv_matches:
                            _word = " & Inventory "
                            kwargs["inv_db"] = True
                        else:
                            _word = " "
                        econsole.print(f":arrows_clockwise: Updating Device{_word}Cache.")
                        self.check_fresh(refresh=True, dev_type=dev_type, **kwargs)
                        cache_updated = True  # Need this for scenario when dev_type is the only thing refreshed, as that does not update self.responses.dev
                        if inv_matches:
                            continue

            if matches:
                out = [CacheDevice(dev.to_dict()) for dev in matches]
                break
            if inv_matches:
                out = [CacheInvDevice(dev.to_dict()) for dev in inv_matches]
                break

        # handle stacks
        if len(out) > 1 and (swack or swack_only):
            unique_swack_ids = set([d.swack_id for d in out if d.swack_id])
            stacks = [d for d in out if d.swack_id in unique_swack_ids and (d.ip or (d.switch_role and d.switch_role == 2))]
            if swack:
                out = [*stacks, *[d for d in out if not d.swack_id]]
            elif swack_only:
                out = stacks

        if completion:
            return out or []

        if out:  # user selects which device if multiple out found
            if len(out) > 1:  # pragma: no cover  requires tty
                out = self.handle_multi_match(sorted(out, key=lambda m: m.get("name", "")), query_str=query_str,)

            return out[0]

        elif retry:  # No match found.  If retry=False will return None on lack of match
            log.error(f"Unable to gather device info from provided identifier [cyan]{query_str}[/]", show=not silent)  # TODO should have log_print retain styling and only strip for log
            if all_matches:
                log.error(
                    f"The Following {len(all_matches)} devices matched {utils.summarize_list([CacheDevice(d.to_dict()) for d in all_matches])} excluded as device type != {escape(str(utils.unlistify(dev_type)))}",
                    show=True,
                )
            if exit_on_fail:
                raise typer.Exit(1)

    @typed_lru_cache
    def get_inv_identifier(
        self,
        query_str: str | Iterable[str],
        *,
        serial_numbers: tuple[str] | None = None,
        dev_type: constants.LibAllDevTypes | Iterable[constants.LibAllDevTypes] = None,
        retry: bool = True,
        completion: bool = False,
        silent: bool = False,
        exit_on_fail: bool = True,
    ) -> CacheInvDevice | list[CacheInvDevice]:
        """Get Devices from local cache, starting with most exact match, and progressively getting less exact.

        This method will serach for a match in the Inventory DB (GreenLake Inventory), then if no match is found,
        it will search Device DB (Central Monitoring/UI), which would provide the serial # to then search the Inventory DB

        Args:
            query_str (str | Iterable[str]): The query string or Iterable of strings to attempt to match.  Iterable will be joined with ' ' to form a single string with spaces.
            serial_numbers (tuple[str], optional): A full list of all serials that are expected to be looked up.
                This is used to do an efficient cache refresh only involving the serials of interest. Defaults to None.
                Note: If any of the serial numbers do not appear to be serial numbers they are ignored, resulting in a full cache update.
            dev_type (Literal["ap", "cx", "sw", "switch", "gw"] | list[Iterable["ap", "cx", "sw", "switch", "gw"]], optional): Limit matches to specific device type. Defaults to None (all device types).
            retry (bool, optional): If failure to match should result in a cache update and retry. Defaults to True.
            completion (bool, optional): If this is being called for tab completion (Allows multiple matches, implies retry=False, silent=True, exit_on_fail=False). Defaults to False.
            silent (bool, optional): Do not display errors / output, simply returns match if match is found. Defaults to False.
            include_inventory (bool, optional): Whether match attempt should also include Inventory DB (devices in GLCP that have yet to connect to Central). Defaults to False.
            exit_on_fail (bool, optional): Whether a failure to match exits the program. Defaults to True.

        Raises:
            typer.Exit: Will display error message and exit if no match is found (unless completion=True or exit_on_fail=False)

        Returns:
            CacheInvDevice | list[CacheInvDevice] | None: if completion = True returns list[CacheInvDevice] containing all matches or None if there was no match.
                Otherwise return will be the CacheInvDevice that matched.  (If completion=False and multiple matches are found, user is prompted to select)
        """
        retry = False if completion else retry
        if dev_type:
            dev_type = utils.listify(dev_type)
            if "switch" in dev_type:
                dev_type = list(set(filter(lambda t: t != "switch", [*dev_type, "cx", "sw"])))

        if isinstance(query_str, (list, tuple)):
            query_str = " ".join(query_str)

        mac_exact = mac_fuzzy = ()
        if utils.Mac(query_str, fuzzy=True):
            mac_exact = (InventoryDevice.mac == utils.Mac(query_str).cols.lower(),)
            mac_fuzzy = (InventoryDevice.mac.istartswith(utils.Mac(query_str, fuzzy=completion).cols.lower()),)

        matches: list[InventoryDevice] = []
        all_matches: list[InventoryDevice] = []
        out: list[CacheInvDevice] = []
        for _ in range(0, 2 if retry else 1):
            # these need to be inside the for loop for secondary lookup using dev.serial if monitoring cache identifier is used
            statements = [
                select(InventoryDevice).where(or_(InventoryDevice.id == query_str, InventoryDevice.serial == query_str, *mac_exact)),
                select(InventoryDevice).where(or_(InventoryDevice.id == query_str.lower(), InventoryDevice.serial == query_str.upper())),  # case insensitive match
                select(InventoryDevice).where(or_(InventoryDevice.id.istartswith(query_str), InventoryDevice.serial.istartswith(query_str), *mac_fuzzy)),  # case insensitive startswith match
            ]
            with Session(self.engine) as session:
                for stmt in statements:
                    matches = session.scalars(stmt).all()
                    if matches:
                        break

                # Try Monitoring DB may be using non inventory field
                if not matches and _ == 0:
                    dev: CacheDevice | None = self.get_dev_identifier(query_str, dev_type=dev_type, silent=True, retry=False, swack=True, exit_on_fail=False)
                    if dev:
                        query_str = dev.serial
                        continue

                if matches and dev_type:
                    all_matches = matches.copy()
                    matches = [d for d in matches if d.type in dev_type]

                # no match found initiate cache update
                if retry and not matches and not (self.responses.inv and set(self.responses.device_type or []) == set(dev_type or [])):
                    if not silent:
                        _msg = "[bright_red]No Match found[/] in Inventory Cache"
                        dev_type_sfx = "" if not dev_type else f" [dim italic](Device Type: {utils.unlistify(dev_type)})[/]"
                        econsole.print(f"{emoji.warn} {_msg} for [cyan]{query_str}[/]{dev_type_sfx}.")
                    if FUZZ and self.inventory and not silent:  # pragma: no cover  requires tty
                        if dev_type:
                            inv_generator = {"id": (d["id"] for d in self.inventory if "id" in d and d["type"] in dev_type), "serial": (d["serial"] for d in self.inventory if "serial" in d and d["type"] in dev_type)}
                        else:
                            inv_generator = {"id": (d["id"] for d in self.inventory if "id" in d), "serial": (d["serial"] for d in self.inventory if "serial" in d)}

                        fuzz_match, fuzz_confidence = None, 0
                        for _field, inv_devices in inv_generator.items():
                            _fuzz_match = process.extractOne(query_str, inv_devices)
                            if _fuzz_match:
                                _match, _confidence = _fuzz_match
                                if _confidence > fuzz_confidence:
                                    field, fuzz_match, fuzz_confidence = _field, _match, _confidence

                        if fuzz_confidence >= 70:
                            confirm_str = render.rich_capture(f"Did you mean [green3]{fuzz_match}[/]?")
                            if typer.confirm(confirm_str):
                                matches = session.scalars(select(InventoryDevice).where(getattr(InventoryDevice, field) == fuzz_match)).all()

                    if not matches:
                        econsole.print(":arrows_clockwise: Updating Inventory Cache.")
                        self.check_fresh(refresh=True, inv_db=True, dev_type=dev_type, serial_numbers=serial_numbers)

                if matches:
                    out = [CacheInvDevice(dev.to_dict()) for dev in matches]
                    break

        if completion:
            return out

        if out:
            if len(out) > 1:
                out = self.handle_multi_match(sorted(out, key=lambda m: m.get("serial", "")), query_str=query_str,)

            return out[0]

        log.error(f"Unable to gather inventory info from provided identifier {query_str}", show=not silent)
        if retry:
            if all_matches:
                log.error(
                    f"The Following {len(all_matches)} devices matched {utils.summarize_list([CacheInvDevice(dev.to_dict()) for dev in all_matches])} excluded as device type != {escape(str(utils.unlistify(dev_type)))}",
                    show=True,
                )
            if exit_on_fail:
                raise typer.Exit(1)

    @typed_lru_cache
    def get_combined_inv_dev_identifier(
        self,
        query_str: str | Iterable[str],
        *,
        serial_numbers: tuple[str] = None,
        dev_type: constants.LibAllDevTypes | Iterable[constants.LibAllDevTypes] = None,
        retry_inv: bool = True,
        retry_dev: bool = True,
        completion: bool = False,
        silent: bool = False,
        exit_on_fail: bool = None,
        exit_on_inv_fail: bool = None,
        exit_on_dev_fail: bool = None,
    ) -> CacheInvMonDevice | list[CacheInvMonDevice]:
        """Searches both Inv Cache and Dev (Monitoring Cache) and returns a CacheInvMonDevice with attributes from both.

        Args:
            query_str (str | Iterable[str]): The query string to use to lookup device details. typically serial,mac,ip,hostname.
            serial_numbers (tuple[str], optional): A full list of all serials that are expected to be looked up.  This is used to do an efficient cache refresh only involving the serials of interest. Defaults to None.
            dev_type (constants.LibAllDevTypes | Iterable[constants.LibAllDevTypes], optional): Device Type of the device being looked up. Defaults to None.
            retry_inv (bool, optional): Determines if an API call is performed to update inventory cache if no match is found. Defaults to True.
            retry_dev (bool, optional): Determines if an API call is performed to update devcice/monitoring cache if no match is found. Defaults to True.
            completion (bool, optional): Indicates lookup is being done for shell completion (implies silent=True, retry=False, exit_on_fail=False). Defaults to False.
            silent (bool, optional): Impacts if messaging is displayed to stderr on failure to match, and when refresh is triggerred. Defaults to False.
            exit_on_fail (bool, optional): Exit if no match is found (inv or dev). Defaults to None, Effectively True if no exit_on args are bool.
            exit_on_inv_fail (bool, optional): Exit if no match is found in Inventory Cache. Defaults to None.
            exit_on_dev_fail (bool, optional): Exit if no match is found in Device/Monitoring Cache. Defaults to None.

        Raises:
            ValueError: Raised if exit_on_fail conflicts with exit_on_inv_fail or exit_on_dev_fail.  exit_on_fail implies both exit_on_inv_fail and exit_on_dev_fail, i.e. exit_on_fail=True w/ exit_on_inv_fail=False is a conflict.

        Returns:
            CacheInvMonDevice | list[CacheInvMonDevice]: Will normally return CacheInvMonDevice if a match is found.  list[CacheInvMonDevice] if completion=True (all matches), can return None or have None in the returned list if exit_on_fail=False
        """
        exit_vars = [exit_on_inv_fail, exit_on_dev_fail]
        if exit_on_fail is not None:
            if any([item is not exit_on_fail for item in exit_vars if item is not None]):
                raise ValueError("exit_on_fail is for both inv and dev. exit_on_inv_fail and exit_on_dev_fail should not conflict")
            exit_on_inv_fail = exit_on_dev_fail = exit_on_fail
        elif exit_vars.count(None) == 2:
            exit_on_inv_fail = exit_on_dev_fail = True

        for idx in range(0, 2):
            inv_dev = self.get_inv_identifier(query_str, serial_numbers=serial_numbers, dev_type=dev_type, retry=retry_inv, completion=completion, silent=True if idx == 0 else silent, exit_on_fail=False if idx == 0 else exit_on_inv_fail)
            if not inv_dev:
                mon_dev: CacheDevice | None = self.get_dev_identifier(query_str, dev_type=dev_type, retry=retry_dev, completion=completion, silent=True, exit_on_fail=exit_on_dev_fail)
                if mon_dev:
                    query_str = mon_dev.serial  # If they provide an identifier only available in Device Table we use it to get the serial for the InventoryDevice lookup
            else:
                mon_dev = self.get_dev_identifier(inv_dev.serial, dev_type=dev_type, retry=retry_dev, completion=completion, silent=True, exit_on_fail=exit_on_dev_fail)
                return CacheInvMonDevice(inv_dev, mon_dev)

    @overload
    def get_site_identifier(
        self,
        query_str: str | Sequence[str],
        retry: Optional[bool],
        completion: bool,
        silent: Optional[bool],
        exit_on_fail: Optional[bool],
    ) -> list[CacheSite]:
        ...  # pragma: no cover

    @overload
    def get_site_identifier(
        self,
        query_str: str | Sequence[str],
        completion: Literal[True]
    ) -> list[CacheSite]: ...  # pragma: no cover

    @overload
    def get_site_identifier(
        self,
        query_str: str | Sequence[str],
    ) -> CacheSite: ...  # pragma: no cover

    @overload
    def get_site_identifier(
        self,
        query_str: str | Sequence[str],
        retry: Optional[bool],
        completion: Optional[bool],
        silent: Optional[bool],
        exit_on_fail: bool,
    ) -> CacheSite | None: ...  # pragma: no cover

    # @typed_lru_cache
    def get_site_identifier(
        self,
        query_str: str | Sequence[str],
        retry: Optional[bool] = True,
        completion: Optional[bool] = False,
        silent: Optional[bool] = False,
        exit_on_fail: Optional[bool] = True,
    ) -> CacheSite | list[CacheSite] | None:
        retry = False if completion else retry
        if isinstance(query_str, (list, tuple)):
            query_str = " ".join(query_str)
        elif not isinstance(query_str, str):
            query_str = str(query_str)

        if not query_str and completion:
            return list(self.sites)

        statements = [
            select(Site).where(or_(Site.name == query_str, cast(Site.id, String) == query_str)),  # exact
            select(Site).where(or_(cast(Site.zip, String) == query_str, Site.address == query_str, Site.city == query_str, Site.state == query_str)),  # exact for address fields
            select(Site).where(or_(func.lower(Site.name) == func.lower(query_str), func.lower(Site.address) == func.lower(query_str), func.lower(Site.city) == func.lower(query_str), func.lower(Site.state) == func.lower(query_str))),  # case insensitive
            select(Site).where(Site.name.like(query_str.replace("-", "_"))),  # _ is wildcard for like() ... match ignoring - and _
            select(Site).where(or_(Site.name.istartswith(query_str.replace("-", "_")), cast(Site.zip, String).istartswith(query_str), Site.city.istartswith(query_str), Site.address.ilike(f"%{query_str}%"))),
        ]

        matches = []
        out: list[CacheSite] = []
        with Session(self.engine) as session:
            for _ in range(0, 2 if retry else 1):
                for stmt in statements:
                    matches = session.scalars(stmt).all()
                    if matches:
                        break

                # err_console.print(f'\n{match=} {query_str=} {retry=} {completion=} {silent=}')  # DEBUG
                if retry and not matches and not self.responses.site:
                    econsole.print(f"{emoji.warn} [bright_red]No Match found[/] for [cyan]{query_str}[/].")
                    if FUZZ and self.sites and not silent:  # pragma: no cover requires tty
                        matches = self.fuzz_lookup(query_str, table=Site, cache_object=CacheSite)
                    if not matches:
                        econsole.print(":arrows_clockwise: Updating [cyan]site[/] Cache")
                        self.check_fresh(refresh=True, site_db=True)
                if matches:
                    out = [CacheSite(s.to_dict()) for s in matches]
                    break

        if completion:
            return out

        if out:
            if len(out) > 1:  # pragma: no cover  Requires tty
                out = self.handle_multi_match(out, query_str=query_str, query_type="site",)

            return out[0]

        log.error(f"Unable to gather site info from provided identifier {query_str}", show=not silent)
        if retry and exit_on_fail:
            raise typer.Exit(1)

    @overload
    def get_group_identifier(
        self,
        query_str: str,
        dev_type: Optional[list[constants.DeviceTypes] | constants.DeviceTypes],
        completion: bool,
    ) -> list[CacheGroup]: ...  # pragma: no cover

    @overload
    def get_group_identifier(
        self,
        query_str: str,
        dev_type: Optional[list[constants.DeviceTypes] | constants.DeviceTypes] = None,
        retry: Optional[bool] = True,
        silent: Optional[bool] = False,
    ) -> CacheGroup: ...  # pragma: no cover

    @overload
    def get_group_identifier(
        self,
        query_str: str,
        exit_on_fail: Literal[False],
    ) -> CacheGroup | None: ...  # pragma: no cover

    @overload
    def get_group_identifier(
        self,
        query_str: str,
        dev_type: Optional[list[constants.DeviceTypes] | constants.DeviceTypes],
        retry: Optional[bool],
        silent: Optional[bool],
        exit_on_fail: Literal[False],
    ) -> CacheGroup | None: ...  # pragma: no cover

    # TODO change all get_*_identifier functions to continue to look for matches when match is found when
    #       completion is True
    def get_group_identifier(
        self,
        query_str: str,
        dev_type: Optional[list[constants.DeviceTypes] | constants.DeviceTypes] = None,
        retry: Optional[bool] = True,
        completion: Optional[bool] = False,
        silent: Optional[bool] = False,
        exit_on_fail: Optional[bool] = True,
    ) -> CacheGroup | list[CacheGroup] | None:
        """Allows Case insensitive group match"""
        retry = False if completion else retry

        if dev_type is not None:
            dev_type = utils.listify(dev_type)
            if "switch" in dev_type:
                dev_type = list(set(filter(lambda t: t != "switch", [*dev_type, "cx", "sw"])))

        if query_str == "":
            if dev_type:
                return [g for g in self.groups if any([_type in g.allowed_types for _type in dev_type])]
            return self.groups

        matches = []
        all_matches = []
        with Session(self.engine) as session:
            for _ in range(0, 2 if retry else 1):
                statements = [
                    select(Group).where(Group.name == query_str),  # exact
                    select(Group).where(Group.name.like(query_str.replace("-", "_"))),  # _ is wildcard for like() ... match ignoring - and _
                    select(Group).where(Group.name.istartswith(query_str)),  # case insensitive startswith
                    select(Group).where(Group.name.ilike(f'%{query_str.replace("-", "_")}%'))  # case insensitive substr ignoring -_
                ]
                for stmt in statements:
                    this_match = session.scalars(stmt).all()
                    matches = [*matches, *[m for m in this_match if m not in matches]]
                    if matches and not completion:
                        break

                if matches and dev_type:
                    all_matches = [CacheGroup(g.to_dict()) for g in matches]
                    matches = [d for d in all_matches if bool([t for t in d.allowed_types if t in dev_type])]

                if not matches and retry and self.responses.group is None:
                    dev_type_sfx = "" if not dev_type else f" [dim italic](Device Type: {utils.unlistify(dev_type)})[/]"
                    econsole.print(f"{emoji.warn} [bright_red]No Match found for[/] [cyan]{query_str}[/]{dev_type_sfx}.")
                    if FUZZ and self.groups and not silent:    # pragma: no cover  Requires tty
                        if dev_type:
                            fuzz_match, fuzz_confidence = process.extract(query_str, [g["name"] for g in self.groups if "name" in g and bool([t for t in g["allowed_types"] if t in dev_type])], limit=1)[0]
                        else:
                            fuzz_match, fuzz_confidence = process.extract(query_str, [g["name"] for g in self.groups], limit=1)[0]
                        confirm_str = render.rich_capture(f"Did you mean [green3]{fuzz_match}[/]?")
                        if fuzz_confidence >= 70 and typer.confirm(confirm_str):
                            matches = session.scalars(select(Group).where(Group.name == fuzz_match)).all()
                    if not matches:
                        econsole.print(":arrows_clockwise: Updating [cyan]group[/] Cache")
                        self.check_fresh(refresh=True, group_db=True)

                if matches:
                    matches = [CacheGroup(g if not hasattr(g, "to_dict") else g.to_dict()) for g in matches]
                    break

        if completion:
            return matches

        if matches:
            if len(matches) > 1:  # pragma: no cover  Requires tty
                matches = self.handle_multi_match(matches, query_str=query_str, query_type="group",)

            return matches[0]

        log.error(f"Unable to gather group data from provided identifier {query_str}", show=not silent)
        if retry:
            if all_matches:
                _dev_type_str = escape(str(utils.unlistify(dev_type)))
                all_match_msg = utils.summarize_list([f"{m.name}|allowed types: {m.allowed_types}" for m in all_matches], pad=0)
                log.error(
                    f"The Following groups matched {all_match_msg} excluded as group not configured for any of {_dev_type_str}",
                    show=True,
                )

            if exit_on_fail:
                valid_groups = utils.summarize_list(self.group_names, max=50)
                econsole.print(f"{emoji.warn} [cyan]{query_str}[/] appears to be [red]invalid[/]")
                econsole.print(f"Valid Groups:\n{valid_groups}")
                raise typer.Exit(1)

    @overload
    def get_template_identifier(self, query_str: str, completion: Literal[True]) -> list[CacheTemplate]: ...  # pragma: no cover

    @overload
    def get_template_identifier(self, query_str: str) -> CacheTemplate: ...  # pragma: no cover

    @overload
    def get_template_identifier(self, query_str: str, retry: Literal[False]) -> CacheTemplate | None: ...  # pragma: no cover

    def get_template_identifier(
        self,
        query_str: str,
        group: str | list[str] = None,
        retry: bool = True,
        completion: bool = False,
        silent: bool = False,
    ) -> CacheTemplate | list[CacheTemplate] | None:
        """Allows case insensitive template match by template name"""
        retry = False if completion else retry
        if not query_str and completion:
            return list(self.templates)

        statements = [
            select(Template).where(Template.name == query_str),  # exact
            select(Template).where(Template.name.like(query_str)),  # _ is wildcard for like() ... match ignoring - and _
            select(Template).where(Template.name.istartswith(query_str)),  # exact
            select(Template).where(Template.name.ilike(f'%{query_str.replace("-", "_")}%'))  # case insensitive substr ignoring -_
        ]

        matches: list[Template] = []
        all_matches: list[Template] = []
        out: list[CacheTemplate] = []
        with Session(self.engine) as session:
            for _ in range(0, 2 if retry else 1):
                for stmt in statements:
                    this_match = session.scalars(stmt).all()
                    matches = [*matches, *[m for m in this_match if m not in matches]]
                    if matches and not completion:
                        break

                if matches and group:
                    all_matches = matches.copy()
                    matches = [d for d in matches if d.group == group]

                if retry and not matches and self.responses.template is None:
                    econsole.print(f"{emoji.warn} [bright_red]No Match found for[/] [cyan]{query_str}[/].")
                    if FUZZ and not silent:  # pragma: no cover  Requires tty
                        matches = self.fuzz_lookup(query_str, table=Template, cache_object=CacheTemplate, group=group)
                    if not matches:
                        econsole.print(":arrows_clockwise: Updating template Cache")
                        self.check_fresh(refresh=True, template_db=True)
                if matches:
                    out = [CacheTemplate(tmplt.to_dict()) for tmplt in matches]
                    break

        if completion:
            return out

        if out:
            if len(out) > 1:  # pragma: no cover  Requires tty
                out = self.handle_multi_match(
                    out,
                    query_str=query_str,
                    query_type="template",
                )
            return out[0]

        log.error(f"Unable to gather template from provided identifier {query_str}", show=not silent, log=silent)
        if retry:
            if all_matches:
                log.error(
                    f"The Following templates matched: {utils.summarize_list([CacheTemplate(t.to_dict()) for t in all_matches])}\n  [red]Excluded[/] as they are not in [cyan]{group}[/] group ",
                    show=True,
                )
            raise typer.Exit(1)

    @overload
    def get_client_identifier(self, query_str: str, completion: Literal[False]) -> CacheClient: ...  # pragma: no cover

    @overload
    def get_client_identifier(self, query_str: str, exit_on_fail: bool = Literal[True]) -> CacheClient: ...  # pragma: no cover

    def get_client_identifier(
        self,
        query_str: str,
        retry: bool = True,
        completion: bool = False,
        exit_on_fail: bool = False,
        silent: bool = False,
    ) -> CacheClient | list[CacheClient]:
        """Search for Client in DB matching on name, ip or mac

        Allows partial and case insensitive match
        """
        retry = False if completion else retry
        if isinstance(query_str, (list, tuple)):
            query_str = " ".join(query_str)

        if completion and not query_str.strip():
            return list(self.clients)

        statements = [
            select(Client).where(or_(Client.name == query_str, Client.ip == query_str, Client.mac == utils.Mac(query_str).cols.lower())),  # exact
            select(Client).where(func.lower(Client.name) == func.lower(query_str)),
            select(Client).where(or_(Client.name.istartswith(query_str), Client.mac.istartswith(utils.Mac(query_str, fuzzy=completion).cols.lower()))),
            select(Client).where(Client.name.like(query_str.replace("-", "_"))),  # _ is wildcard for like() ... match ignoring - and _
            select(Client).where(Client.name.ilike(f'%{query_str.replace("-", "_")}%'))  # case insensitive substr ignoring -_
        ]

        matches: list[Client] = []
        out: list[CacheClient] = []
        with Session(self.engine) as session:
            for _ in range(0, 2 if retry else 1):
                for idx, stmt in enumerate(statements):
                    this_match = session.scalars(stmt).all()
                    matches = [*matches, *[m for m in this_match if m not in matches]]
                    if matches and (idx <= 1 or not completion):  # query 0 and 1 are more exact matches  # TODO consider this logic in other get_identifier funcs
                        break

                # no match found try fuzzy match (typos) and initiate cache update
                if retry and not matches and self.responses.client is None:
                    econsole.print(f"{emoji.warn} [bright_red]No Match found[/] for [cyan]{query_str}[/].")
                    if FUZZ and not silent:
                        matches = self.fuzz_lookup(query_str, table=Client, cache_object=CacheClient)
                    if not matches:  # on demand update only for WLAN as roaming and kick only applies to WLAN currently
                        econsole.print(":arrows_clockwise: Updating [dim italic](Wireless)[/] [cyan]client[/] Cache")
                        api.session.request(self.refresh_client_db, "wireless")

                if matches:
                    out = [CacheClient(c.to_dict()) for c in matches]
                    break

        if completion:
            return out

        if out:
            if len(out) > 1:  # pragma: no cover  Requires tty
                out = self.handle_multi_match(out, query_str=query_str, query_type="client")
            return out[0]

        if retry:
            log.error(f"Unable to gather client info from provided identifier {query_str}", show=not silent)
            if exit_on_fail:
                raise typer.Exit(1)

    def get_audit_log_identifier(self, query: str) -> str:
        if "audit_trail" in query:
            return query

        try:
            with Session(self.engine) as session:
                match = session.scalars(select(CentralAuditLog).where(CentralAuditLog.id == int(query))).all()
            if not match:
                log.warning(f"\nUnable to gather log id from short index query [cyan]{query}[/]", show=True)
                econsole.print("Short log_id aliases are built each time [cyan]show logs[/] / [cyan]show audit logs[/]... is ran.")
                econsole.print("  repeat the command without specifying the log_id to populate the cache.")
                econsole.print("  You can verify the cache by running [dim italic](hidden command)[/] [cyan]show cache logs[/]")
                raise typer.Exit(1)
            else:
                return match[-1].long_id

        except ValueError as e:
            econsole.print(f"{emoji.warn} [bright_red]{e.__class__.__name__}[/]:  Expecting an intiger for log_id. '{query}' does not appear to be an integer.")
            raise typer.Exit(1)

    def get_event_log_identifier(self, query: str) -> dict:
        """Get event log details based on identifier.

        Args:
            query (str): The short event log id, generated anytime show logs is ran for any events
                that have details.

        Raises:
            typer.Exit: If unable to find id, or the id is not a valid type

        Returns:
            dict: Dictionary containing event log details.
        """
        try:
            with Session(self.engine) as session:
                match = session.scalars(select(Event).where(Event.id == str(query))).all()  # TODO make id an int in the cache so consistent with audit logs
            if not match:
                log.warning(f"Unable to gather event details from short index query {query}", show=True)
                econsole.print("Short event_id aliases are built each time [cyan]show logs[/] is ran.")
                econsole.print("  You can verify the cache by running [dim italic](hidden command)[/] [cyan]show cache events[/]")
                econsole.print("  run [cyan]show logs [OPTIONS][/] then use the short index for details")
                raise typer.Exit(1)
            else:
                return match[-1].details

        except ValueError as e:
            log.error(f"Exception in get_event_identifier {e.__class__.__name__}", show=True)
            raise typer.Exit(1)

    @overload
    def get_mpsk_network_identifier(
        self,
        query_str: str,
        retry: bool = True,
        completion: bool = True,
        silent: bool = False,
    ) -> list[CacheMpskNetwork]: ...  # pragma: no cover

    @overload
    def get_mpsk_network_identifier(
        self,
        query_str: str,
        retry: bool = True,
        completion: bool = False,
        silent: bool = False,
    ) -> CacheMpskNetwork: ...  # pragma: no cover

    def get_mpsk_network_identifier(
        self,
        query_str: str,
        retry: bool = True,
        completion: bool = False,
        silent: bool = False,
    ) -> CacheMpskNetwork | list[CacheMpskNetwork]:
        """Allows Case insensitive ssid match"""
        retry = False if completion else retry
        if not query_str and completion:
            return list(self.mpsk_networks)

        statements = [
            select(MPSKNetwork).where(or_(MPSKNetwork.name == query_str, MPSKNetwork.id.istartswith(query_str))),
            select(MPSKNetwork).where(MPSKNetwork.name.istartswith(query_str)),
            select(MPSKNetwork).where(MPSKNetwork.name.like(query_str.replace("-", "_"))),  # _ is wildcard for like() ... match ignoring - and _
            select(MPSKNetwork).where(MPSKNetwork.name.ilike(f'%{query_str.replace("-", "_")}%'))  # case insensitive substr ignoring -_
        ]

        matches = []
        out: list[CacheMpskNetwork] = []
        with Session(self.engine) as session:
            for _ in range(0, 2 if retry else 1):
                for stmt in statements:
                    this_match = session.scalars(stmt).all()
                    matches = [*matches, *[m for m in this_match if m not in matches]]
                    if matches and not completion:
                        break

                if not matches and retry and self.responses.mpsk_network is None:
                    econsole.print(f"{emoji.warn} [bright_red]No Match found[/] for [cyan]{query_str}[/].")
                    if FUZZ and self.mpsk_networks and not silent:  # pragma: no cover requires tty
                        matches = self.fuzz_lookup(query_str, table=MPSKNetwork, cache_object=CacheMpskNetwork)
                    if not matches:
                        econsole.print(":arrows_clockwise: Updating [cyan]MPSK Networks[/] Cache")
                        api.session.request(self.refresh_mpsk_networks_db)

                if matches:
                    out = [CacheMpskNetwork(net.to_dict()) for net in matches]
                    break

        if completion:
            return out

        if out:
            if len(out) > 1:  # pragma: no cover requires tty
                out = self.handle_multi_match(out, query_str=query_str, query_type="mpsk",)

            return out[0]

        log.error(f"Central API CLI Cache unable to gather MPSK Network data from provided identifier {query_str}", show=not silent or _ == 1)
        if retry:
            valid_mpsk = "\n".join([f'[cyan]{m.name}[/]' for m in self.mpsk_networks])
            econsole.print(f"{emoji.warn} [cyan]{query_str}[/] appears to be invalid")
            econsole.print(f"\n[bright_green]Valid MPSK Networks[/]:\n--\n{valid_mpsk}\n--\n")
            raise typer.Exit(1)

    @staticmethod
    def _handle_sub_multi_match(match: list[CacheSub], *, end_date: dt.datetime, best_match: bool = False, all_sub_matches: bool = False) -> list[CacheSub]:
        if len(match) > 1 and end_date:
            end_date_day = end_date.combine(end_date, dt.time.min)  # subscription expires on the day provided
            match = [m for m in match if dt.datetime.combine(pendulum.from_timestamp(m.end_date), dt.time.min) == end_date_day]
            if len(match) > 1 and end_date_day != end_date:  # if still too many matches check for exact match if they provided time info.
                match = [m for m in match if pendulum.from_timestamp(m.end_date) == end_date]

        if len(match) > 1:
            valid_match = [m for m in match if m.valid]  # valid means it is not expired and has subscriptions available
            match = valid_match or match

        if best_match or all_sub_matches:
            sorted_match = sorted(match, key=lambda m: (m.end_date, m.available), reverse=True)
            match = sorted_match if all_sub_matches else [sorted_match[0]]

        return match

    # TODO make this a wrapper for other specific get_portal_identifier.... calls
    @typed_lru_cache
    def get_name_id_identifier(
        self,
        cache_name: Literal["dev", "site", "sub", "template", "group", "label", "mpsk_network", "mpsk", "portal", "building"],
        query_str: str,
        retry: bool = True,
        completion: bool = False,
        silent: bool = False,
        end_date: dt.datetime = None,
        best_match: bool = False,
        all_sub_matches: bool = False,
    ) -> CachePortal | list[CachePortal] | CacheLabel | list[CacheLabel] | CacheSub | list[CacheSub]:
        """Fetch items from cache based on query

        This is a common identifier lookup function for all stored types that use name and id as potential match fields.

        DEV NOTE appears only to be used by portal and subscription currently

        Args:
            cache_name (Literal['dev', 'site', 'sub', 'template', 'group', 'label', 'mpsk_network', 'mpsk', 'portal']): The cache to search
            query_str (str): The query string used to search the cache for a match
            retry (bool, optional): Refresh the cache via API and retry if no match is found. Defaults to True.
            completion (bool, optional): Indicates function is being called for CLI completion... effectively the equiv of retry=False, Silent=True. Defaults to False.
            silent (bool, optional): Set to True to squelch out all messaging normmaly displayed when no match is found, and retry is initiated. Defaults to False.
            end_date (dt.datetime, optional): Specific to 'sub' cache.  Provide End Date to further narrow search in the event of multiple subscription matches. Defaults to None.
            best_match (bool, optional): Specific to 'sub' cache.  Set True to return the best match in the event of multiple matches.
                Best match is the valid match with the most time remaining on the subscription. Defaults to False (user is prompted to select one of the matches).
            all_sub_matches (bool, optional): Sepcific to 'sub' cache.  Return all matches in the event of multiple matches. Defaults to False.

        Raises:
            typer.Exit: Terminates program if no match is found.

        Returns:
            CachePortal | list[CachePortal] | CacheLabel | list[CacheLabel] | CacheSub | list[CacheSub] | CacheBuilding | list[CacheBuilding]: The Cache object associated with the provided cache_name.
        """
        retry = False if completion else retry

        cache_details = CacheDetails(self)
        this: CacheAttributes = getattr(cache_details, cache_name)
        name_to_models = {
            "portal": (Portal, CachePortal),
            "label": (Label, CacheLabel),
            "mpsk_network": (MPSKNetwork, CacheMpskNetwork),
            "sub": (Subscription, CacheSub),
            "building": (Building, CacheBuilding)
        }
        cache_updated = False
        _models = name_to_models[cache_name]
        Table: Portal | Label | MPSKNetwork | Subscription = _models[0]
        Model: CachePortal | CacheLabel | CacheMpskNetwork | CacheSub = _models[1]

        if isinstance(query_str, (list, tuple)):
            query_str = " ".join(query_str)
        elif not isinstance(query_str, str):
            query_str = str(query_str)

        statements = [
            select(Table).where(or_(Table.name == query_str, Table.id.istartswith(query_str))),
            select(Table).where(Table.name.istartswith(query_str)),  # exact
            select(Table).where(Table.name.like(query_str.replace("-", "_"))),  # _ is wildcard for like() ... match ignoring - and _
            select(Table).where(Table.name.ilike(f'%{query_str.replace("-", "_")}%'))  # case insensitive substr ignoring -_
        ]

        matches = []
        out: list[CachePortal | CacheLabel | CacheMpskNetwork] = []
        with Session(self.engine) as session:
            db_all: list[Portal | Label | MPSKNetwork | Subscription] = session.scalars(select(Table)).all()
            for _ in range(0, 2 if retry else 1):
                if query_str == "":
                    matches = db_all
                else:
                    for stmt in statements:
                        this_match = session.scalars(stmt).all()
                        matches: list[Portal | Label | MPSKNetwork | Subscription] = [*matches, *[m for m in this_match if m not in matches]]
                        if matches and not completion:
                            break

                if not matches and retry and not cache_updated:
                    econsole.print(f"{emoji.warn} [bright_red]No Match found[/] for [cyan]{query_str}[/].")
                    if FUZZ and db_all and not silent:  # pragma: no cover requires tty
                        matches = self.fuzz_lookup(query_str, table=Table, cache_object=Model)
                    if not matches:
                        econsole.print(f":arrows_clockwise: Updating [cyan]{cache_name}[/] Cache")
                        api.session.request(this.cache_update_func)
                        cache_updated = True

                if matches:
                    out = [Model(m.to_dict()) for m in matches]
                    break

        if completion:
            return out

        if out:
            if cache_name == "sub" and len(out) > 1:
                out = self._handle_sub_multi_match(out, end_date=end_date, best_match=best_match, all_sub_matches=all_sub_matches)  # pragma: no cover
                if all_sub_matches:
                    return out

            if len(out) > 1:
                out = self.handle_multi_match(out, query_str=query_str, query_type=this.name,)

            return out[0]

        log.error(f"Central API CLI Cache unable to gather {cache_name} data from provided identifier {query_str}", show=retry or not silent)
        if retry:
            valid = "\n".join([f'[cyan]{m.name}[/]' for m in db_all])
            econsole.print(f":warning:  [cyan]{query_str}[/] appears to be invalid")
            econsole.print(f"\n[bright_green]Valid Names[/]:\n--\n{valid}\n--\n")
            raise typer.Exit(1)

    @typed_lru_cache
    def get_sub_identifier(
        self,
        query_str: str,
        retry: bool = True,
        completion: bool = False,
        silent: bool = False,
        end_date: dt.datetime = None,
        best_match: bool = False,  # TODO change to default True
        all_sub_matches: bool = False,
    ) -> CacheSub | list[CacheSub] | None:
        """Fetch items from subscription cache based on query

        Args:
            query_str (str): The query string used to search the cache for a match
            retry (bool, optional): Refresh the cache via API and retry if no match is found. Defaults to True.
            completion (bool, optional): Indicates function is being called for CLI completion... effectively the equiv of retry=False, Silent=True. Defaults to False.
            silent (bool, optional): Set to True to squelch out all messaging normmaly displayed when no match is found, and retry is initiated. Defaults to False.
            end_date (dt.datetime, optional): Specific to 'sub' cache.  Provide End Date to further narrow search in the event of multiple subscription matches. Defaults to None.
            best_match (bool, optional): Specific to 'sub' cache.  Set True to return the best match in the event of multiple matches.
                Best match is the valid match with the most time remaining on the subscription. Defaults to False (user is prompted to select one of the matches).
            all_sub_matches (bool, optional): Sepcific to 'sub' cache.  Return all matches in the event of multiple matches. Defaults to False.

        Raises:
            typer.Exit: Terminates program if no match is found.

        Returns:
            CachePortal | list[CachePortal] | CacheLabel | list[CacheLabel] | CacheSub | list[CacheSub]: The Cache object associated with the provided cache_name.
        """
        cache_updated = False
        retry = False if completion else retry

        if isinstance(query_str, (list, tuple)):
            query_str = " ".join(query_str)
        elif not isinstance(query_str, str):
            query_str = str(query_str)

        matches = []
        out: list[CacheSub] = []
        with Session(self.engine) as session:
            db_all: list[Subscription] = session.scalars(select(Subscription)).all()
            for _ in range(0, 2 if retry else 1):
                if query_str == "":
                    matches = db_all
                else:
                    statements = [
                        select(Subscription).where(or_(Subscription.name == query_str, Subscription.key.istartswith(query_str), Subscription.id.istartswith(query_str))),
                        select(Subscription).where(Subscription.name.istartswith(query_str)),  # exact
                        select(Subscription).where(Subscription.name.like(query_str.replace("-", "_"))),  # _ is wildcard for like() ... match ignoring - and _
                        select(Subscription).where(Subscription.name.ilike(f'%{query_str.replace("-", "_")}%')),  # case insensitive substr ignoring -_
                        select(Subscription).where(Subscription.name.ilike(f'%{query_str.replace("-", "_").lower().replace("advanced", "advance%")}%')),
                    ]
                    for stmt in statements:
                        this_match = session.scalars(stmt).all()
                        matches: list[Subscription] = [*matches, *[m for m in this_match if m not in matches]]
                        if matches and not completion:
                            break

                if not matches and retry and not cache_updated:
                    econsole.print(f"[dark_orange3]:warning:[/]  [bright_red]No Match found[/] for [cyan]{query_str}[/].")
                    if FUZZ and db_all and not silent:  # pragma: no cover requires tty
                        matches = self.fuzz_lookup(query_str, table=Subscription, cache_object=CacheSub)
                    if not matches:
                        econsole.print(":arrows_clockwise: Updating [cyan]Subscription[/] Cache")
                        api.session.request(self.refresh_sub_db)
                        cache_updated = True

                if matches:
                    out = [CacheSub(m.to_dict()) for m in matches]
                    break

        if completion:
            return out

        if out:
            if len(out) > 1:
                out = self._handle_sub_multi_match(out, end_date=end_date, best_match=best_match, all_sub_matches=all_sub_matches)
                if all_sub_matches:
                    return out

            if len(out) > 1:
                out = self.handle_multi_match(out, query_str=query_str, query_type="sub",)  # pragma: no cover

            return out[0]

        log.error(f"Central API CLI Cache unable to gather Subscription data from provided identifier {query_str}", show=retry or not silent)
        if retry:
            econsole.print(f":warning:  [cyan]{query_str}[/] appears to be invalid")
            econsole.print(f"\n[bright_green]Available Subscriptions[/]:\n--\n{utils.summarize_list(list(self.subscriptions), max=None, pad=0)}\n--\n")
            raise typer.Exit(1)

    @overload
    def get_label_identifier(
        self,
        query_str: str,
    ) -> CacheLabel: ...  # pragma: no cover

    @overload
    def get_label_identifier(
        self,
        query_str: str,
        retry: Optional[bool],
        completion: Optional[Literal[False]],
        silent: Optional[bool],
    ) -> CacheLabel: ...  # pragma: no cover

    @overload
    def get_label_identifier(
        self,
        query_str: str,
        retry: Optional[bool],
        completion: Literal[True],
        silent: Optional[bool],
    ) -> list[CacheLabel]: ...  # pragma: no cover

    def get_label_identifier(
        self,
        query_str: str,
        retry: bool = True,
        completion: bool = False,
        silent: bool = False,
    ) -> CacheLabel | list[CacheLabel]:
        return self.get_name_id_identifier("label", query_str, retry=retry, completion=completion, silent=silent)

    def get_portal_identifier(
        self,
        query_str: str,
        retry: bool = True,
        completion: bool = False,
        silent: bool = False,
    ) -> CachePortal | list[CachePortal]:
        return self.get_name_id_identifier("portal", query_str, retry=retry, completion=completion, silent=silent)


class CacheAttributes:
    def __init__(self, name: Literal["dev", "site", "template", "group", "label", "portal", "mpsk", "mpsk_network", "sub"], cache_update_func: Callable) -> None:
        self.name = name
        self.cache_update_func = cache_update_func


class CacheDetails:
    def __init__(self, cache=Cache):
        self.label = CacheAttributes(name="label", cache_update_func=cache.refresh_label_db)
        self.portal = CacheAttributes(name="portal", cache_update_func=cache.refresh_portal_db)
        self.mpsk_network = CacheAttributes(name="mpsk_network", cache_update_func=cache.refresh_mpsk_networks_db)
        self.sub = CacheAttributes(name="sub", cache_update_func=cache.refresh_sub_db)
