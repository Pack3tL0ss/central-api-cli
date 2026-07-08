import json
from enum import Enum
from typing import Any, List, Optional, TypeAlias

from rich.text import Text
from sqlalchemy import JSON, Column, ForeignKey, String, TypeDecorator
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
import pendulum

from centralcli.constants import CertTypes, GroupDevTypes


class EnumListStringType(TypeDecorator):
    """Stores a list of Enums as a list of strings in the DB."""
    impl = String
    cache_ok = True

    def __init__(self, enum_type):
        super().__init__()
        self.enum_type = enum_type

    def process_bind_param(self, value, dialect):
        # Convert list of Enums to a JSON string before storing in DB
        value = [self.enum_type(v if not hasattr(v, "value") else v.value) for v in value]
        if value is not None:
            return json.dumps([item.value for item in value])
        return None

    def process_result_value(self, value, dialect):
        # # Convert JSON string back to list of Enums when reading from DB
        if value is not None:
            # Assumes the values stored in the DB exactly match the enum values
            # return [self.enum_type(item) for item in json.loads(value)]
            return json.loads(value)
        return None


class Base(DeclarativeBase):
    def to_dict(self) -> dict[str, Any]:
        return {field.name: getattr(self, field.name) for field in self.__table__.c}


# This is the same as DevTypes (plural in constants) other than DevTypes includes sdwan.
# Could probably use same model for everything in here.  One or the other.
class DevType(str, Enum):
    ap = "ap"
    sw = "sw"
    cx = "cx"
    gw = "gw"
    sdwan = "sdwan"
    bridge = "bridge"
    sensor = "sensor"


class InventoryDevice(Base):
    __tablename__ = "inventory"
    id: Mapped[Optional[str]] = None
    serial: Mapped[str] = mapped_column(primary_key=True)
    mac: Mapped[str] = mapped_column(String())
    type: Mapped[Optional[str]] = None
    model: Mapped[Optional[str]] = None
    sku: Mapped[Optional[str]] = None
    subscription: Mapped[Optional[str]] = None
    subscription_key: Mapped[Optional[str]] = mapped_column(ForeignKey(("subscriptions.key")), default=None)
    subscription_expires: Mapped[Optional[int]] = None
    assigned: Mapped[Optional[bool]] = None
    archived: Mapped[Optional[bool]] = None
    monitoring = relationship("Device", back_populates="inv")

    def __repr__(self) -> str:  # pragma: no cover
        return f"InventoryDevice({self.type!r}|{self.model!r}|{self.serial!r}|{self.mac!r}) object at {hex(id(self))}"

    def __str__(self) -> str:
        return f"[dark_olive_green2]{self.serial}[/]|[turquoise4]{self.mac}[/]|[cyan]{self.type}[/]|[turquoise4]{self.model} [dim]{self.sku}[/dim][/]|{self._status_str}"

    def __rich__(self) -> str:
        return Text.from_markup(str(self))

    def _status_str(self) -> str:
        if not self.assigned:
            return "[bright_red]Not Assigned to Aruba Central in [green]GreenLake[/green][/]"
        if self.archived:
            return "[bright_red]ARCHIVED [dim italic](in [green]GreenLake[/][/]"
        _sub_str = self.subscription and f"[cyan]{self.subscription}[/]" or "[bright_red]No Subscription Assigned[/]"
        if not self.subscription or pendulum.now().int_timestamp < self.subscription_expires:
            return _sub_str
        return "[bright_red]EXPIRED[/]"


class DeviceStatus(str, Enum):
    Up = "Up"
    Down = "Down"


class Device(Base):
    __tablename__ = "devices"
    name: Mapped[str]
    # status: Mapped[DeviceStatus]
    status: DeviceStatus = Column("status", String, nullable=False)  # needed for SQLAlchemy to honor use_enum_values
    # type: Mapped[DevType]
    type: DeviceStatus = Column("type", String, nullable=False)  # needed for SQLAlchemy to honor use_enum_values
    model: Mapped[str]
    ip: Mapped[str] = mapped_column(nullable=True, default=None)
    serial: Mapped[str] = mapped_column(ForeignKey("inventory.serial"), primary_key=True)
    mac: Mapped[str] = mapped_column(String())
    group: Mapped[str] = mapped_column(ForeignKey("groups.name"))
    site: Mapped[Optional[str]] = mapped_column(ForeignKey("sites.name"), default=None)
    version: Mapped[str]
    swack_id: Mapped[Optional[str]] = None
    switch_role: Mapped[Optional[int]] = None
    inv = relationship("InventoryDevice", back_populates="monitoring")
    # inv_id: Mapped[Optional[str]] = Column(str, ForeignKey("inventory.id"))

    def __repr__(self) -> str:
        return f"Device({self.name!r}|{self.type!r}|{self.model!r}|{self.serial!r}|{self.mac!r}|{self.status!r}) object at {hex(id(self))}"


class Site(Base):
    __tablename__ = "sites"
    name: Mapped[str]
    id: Mapped[int] = mapped_column(primary_key=True)
    address: Mapped[Optional[str]] = None
    city: Mapped[Optional[str]] = None
    state: Mapped[Optional[str]] = None
    zip: Mapped[Optional[str]] = None
    country: Mapped[Optional[str]] = None
    lon: Mapped[Optional[float]] = None
    lat: Mapped[Optional[float]] = None
    devices: Mapped[Optional[int]] = None

    def __repr__(self) -> str:
        parts = [self.address, self.city, self.state, self.zip, self.country]
        parts = [p for p in parts if p is not None] or [self.lat, self.lon]
        return f"Site({self.name!r}|{'|'.join(parts)}|devices: {self.devies}) object at {hex(id(self))}"


class GatewayRole(str, Enum):
    branch = "branch"
    vpnc = "vpnc"
    wlan = "wlan"
    sdwan = "sdwan"
    NA = "NA"


class Group(Base):
    __tablename__ = "groups"
    name: Mapped[str] = mapped_column(primary_key=True)
    allowed_types: Mapped[List[GroupDevTypes]] = Column(EnumListStringType(GroupDevTypes))
    gw_role: Mapped[Optional[GatewayRole]] = Column("gw_role", String)
    aos10: Mapped[Optional[bool]] = None  # TODO may have allowed 'NA'
    microbranch: Mapped[Optional[bool]] = None
    wlan_tg: Mapped[Optional[bool]] = None
    wired_tg: Mapped[Optional[bool]] = None
    monitor_only_sw: Mapped[Optional[bool]] = None
    monitor_only_cx: Mapped[Optional[bool]] = None
    cnx: Mapped[Optional[bool]] = None

    def __repr__(self) -> str:
        return f"Group+({self.name!r}|{self.allowed_types!r}|wlan_tg: {self.wlan_tg!r}|wired_tg: {self.wired_tg!r}) object at {hex(id(self))}"


class Template(Base):
    __tablename__ = "templates"
    name: Mapped[str] = mapped_column(primary_key=True)
    device_type: Mapped[DevType] = mapped_column(String)
    group: Mapped[str] = mapped_column(ForeignKey("groups.name"), primary_key=True)
    model: Mapped[str]
    version: Mapped[str]
    template_hash: Mapped[str]

    def __repr__(self) -> str:
        return f"Template({self.name}|{self.device_type}|g:{self.group}|model: {self.model}|ver: {self.version}) object at {hex(id(self))}"


class Label(Base):
    __tablename__ = "labels"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(index=True)
    devices: Mapped[Optional[int]] = None

    def __repr__(self) -> str:
        return f"Label({self.name!r}|{self.id!r}|devices: {self.devices}) object at {hex(id(self))}"


class ClientType(str, Enum):
    wired = "wired"
    wireless = "wireless"


class Client(Base):
    __tablename__ = "clients"
    mac: Mapped[str] = mapped_column(primary_key=True)
    name: Mapped[str] = None
    ip: Mapped[str] = None
    type: Mapped[ClientType] = mapped_column(String)
    network_port: Mapped[Optional[str]] = None
    connected_serial: Mapped[Optional[str]] = mapped_column(ForeignKey("devices.serial"), default=None)
    connected_name: Mapped[str] = None
    site: Mapped[Optional[str]] = None
    group: Mapped[str] = None
    last_connected: Mapped[int] = mapped_column(default=None, nullable=True)

    def __repr__(self) -> str:
        return f"Client({self.name!r}|{self.mac!r}|s: {self.site}|{self.connected_name}) object at {hex(id(self))}"


class MPSKNetwork(Base):
    __tablename__ = "mpsk_networks"
    id: Mapped[str] = mapped_column(primary_key=True)
    name: Mapped[str]

    def __repr__(self) -> str:
        return f"MPSKNetwork({self.name!r}|{self.id!r}) object at {hex(id(self))}"


class MPSK(Base):
    __tablename__ = "mpsk"
    id: Mapped[str] = mapped_column(primary_key=True)
    name: Mapped[str] = None
    role: Mapped[str] = None
    status: Mapped[str] = None  # enabled or disabled
    ssid: Mapped[str] = None

    def __repr__(self) -> str:
        return f"MPSK({self.name!r}|{self.id!r}|{self.ssid!r}|{self.role!r}|{self.status!r}) object at {hex(id(self))}"


class Subscription(Base):
    __tablename__ = "subscriptions"
    id: Mapped[str] = mapped_column(primary_key=True)
    name: Mapped[str]
    type: Mapped[str]
    key: Mapped[str] = mapped_column(unique=True)
    qty: Mapped[int]
    available: Mapped[int]
    is_eval: Mapped[bool]
    sku: Mapped[str]
    start_date: Mapped[int]
    end_date: Mapped[int]
    started: Mapped[bool]
    expired: Mapped[bool]
    valid: Mapped[bool]

    def __repr__(self) -> str:
        return f"Subscription({self.name!r}|{self.id!r}|{self.key!r}|{self.type!r}|{'OK' if self.valid else 'NOT OK'}) object at {hex(id(self))}"


class SubscriptionName(Base):
    __tablename__ = "licenses"
    name: Mapped[str] = mapped_column(primary_key=True)

    def __repr__(self) -> str:
        return f"ValidSubscription({self.name!r}) object at {hex(id(self))}"


class Building(Base):
    __tablename__ = "floor_plan_buildings"
    id: Mapped[str] = mapped_column(primary_key=True)
    name: Mapped[str]
    campus_id: Mapped[str]
    lat: Mapped[float]
    lon: Mapped[float]

    def __repr__(self) -> str:
        return f"Building({self.name!r}|{self.id!r}|{self.campus_id!r}|{self.lat!r}|{self.lon!r}) object at {hex(id(self))}"


class FloorPlanAP(Base):
    __tablename__ = "floor_plan_aps"
    id: Mapped[str] = mapped_column(primary_key=True)
    name: Mapped[str]
    serial: Mapped[str] = mapped_column(ForeignKey("devices.serial"))
    mac: Mapped[str]
    floor_id: Mapped[str]
    building_id: Mapped[Optional[str]] = mapped_column(ForeignKey("floor_plan_buildings.id"), default=None)
    level: Mapped[Optional[float]] = None  # was int | float

    def __repr__(self) -> str:
        return f"FloorPlanAP({self.name!r}|{self.id!r}|{self.serial!r}|{self.mac!r}) object at {hex(id(self))}"


class GLPService(Base):
    __tablename__ = "services"
    id: Mapped[str] = mapped_column(primary_key=True)
    name: Mapped[str]
    region: Mapped[str]

    def __repr__(self) -> str:
        return f"GLPService({self.name!r}|{self.id!r}|{self.region!r}) object at {hex(id(self))}"


class Cert(Base):
    __tablename__ = "certs"
    name: Mapped[str] = mapped_column(primary_key=True)
    type: Mapped[CertTypes] = mapped_column(String)
    md5_checksum: Mapped[str]
    expired: Mapped[bool]
    expiration: Mapped[int]

    def __repr__(self) -> str:
        return f"Cert({self.name!r}|{self.type!r}|Expired: {self.expired!r}) object at {hex(id(self))}"


class Guest(Base):
    __tablename__ = "guests"
    portal_id: Mapped[str] = mapped_column(ForeignKey("portals.id"))
    name: Mapped[str]
    id: Mapped[str] = mapped_column(primary_key=True)
    email: Mapped[Optional[str]] = None
    phone: Mapped[Optional[str]] = None
    company: Mapped[Optional[str]] = None
    enabled: Mapped[bool]
    status: Mapped[Optional[str]] = None
    created: Mapped[int]
    expires: Mapped[Optional[int]] = mapped_column(default=None)

    def __repr__(self) -> str:
        return f"Guest({self.name!r}|{self.id!r}|portal_id: {self.portal_id!r}|enabled: {self.enabled!r}) object at {hex(id(self))}"


class Portal(Base):
    __tablename__ = "portals"
    name: Mapped[str]
    id: Mapped[str] = mapped_column(primary_key=True)
    url: Mapped[str]
    auth_type: Mapped[str]
    is_aruba_cert: Mapped[bool]
    is_default: Mapped[bool]
    is_editable: Mapped[bool]
    is_shared: Mapped[bool]
    reg_by_email: Mapped[bool]
    reg_by_phone: Mapped[bool]


class CentralAuditLog(Base):
    __tablename__ = "central_audit_logs"
    id: Mapped[str]
    long_id: Mapped[str] = mapped_column(primary_key=True)

    def __repr__(self) -> str:
        return f"CentralAuditLog({self.id!r}|{self.long_id!r}) object at {hex(id(self))}"


class Event(Base):
    __tablename__ = "events"
    id: Mapped[str] = mapped_column(primary_key=True)
    device: Mapped[str]
    details: Mapped[dict] = mapped_column(JSON)

    def __repr__(self) -> str:
        return f"Event({self.id!r}|{self.device!r}) object at {hex(id(self))}"


class WebHookData(Base):
    __tablename__ = "wh_data"
    id: Mapped[str] = mapped_column(primary_key=True)
    ok: Mapped[bool]
    alert_type: Mapped[str]
    device_id: Mapped[str] = mapped_column(ForeignKey("devices.serial"))
    state: Mapped[str]
    text: Mapped[str]
    timestamp: Mapped[int]

    def __repr__(self) -> str:
        return f"WebHookData({self.id!r}|{self.device_id!r}|ok: {self.ok!r}|{self.alert_type!r}|{self.state!r}) object at {hex(id(self))}"


CacheTable: TypeAlias = Device | InventoryDevice | Site | Group | Template | Label | Client | MPSKNetwork | MPSK | Subscription | SubscriptionName | Building | FloorPlanAP | GLPService | Cert | Guest | Portal | CentralAuditLog | Event | WebHookData