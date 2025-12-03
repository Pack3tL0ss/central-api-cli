from __future__ import annotations

from enum import Enum
from typing import Annotated, List, Optional

from pydantic import AliasChoices, BaseModel, BeforeValidator, ConfigDict, Field, RootModel, model_validator
from rich.console import Console
from typing_extensions import Self

from .. import utils
from ..constants import DynamicAntMode, RadioBandOptions


class MpskStatus(str, Enum):
    enabled = "enabled"
    disabled = "disabled"


def _str_to_list(value: str | int | float | List[Enum] | List[str] | List[int, float]) -> None | List[str]:
    """Allows import file to be a space or quoted comma separated str vs. a list

    useful for csv.  A comma seperated str (wrapped in quotes in the csv) is also valid.
    i.e. '2.4 5 6' would return ["2.4", "5", "6"]

    Args:
        value (str | int | float | List[Enum] | List[str] | List[int, float]): The value of the field

    Returns:
        None | List[str]: None if the field is not in the import file or has no value otherwise
            returns a list based on the value(s) provided.
    """
    if value is None:
        return value

    if isinstance(value, list):
        if value and hasattr(value[0], "value"):
            return [v.value for v in value]

        return list(map(str, value))

    if isinstance(value, (int, float)):  # possible with yaml/json import
        return [str(value)]

    if "," in value:
        return [v.strip() for v in map(str, value.split(","))]

    if " " in value:
        return list(map(str, value.split()))

    return utils.listify(value)


class APUpdate(BaseModel):
    model_config = ConfigDict(use_enum_values=True)
    serial: str
    hostname: Optional[str] = None
    ip: Optional[str] = None
    mask: Optional[str] = None
    gateway: Optional[str] = None
    dns: Annotated[List[str], BeforeValidator(_str_to_list)] = None
    domain: Optional[str] = None
    disable_radios: Annotated[List[RadioBandOptions], BeforeValidator(_str_to_list)] = None
    enable_radios: Annotated[List[RadioBandOptions], BeforeValidator(_str_to_list)] = None
    access_radios: Annotated[List[RadioBandOptions], BeforeValidator(_str_to_list)] = None
    monitor_radios: Annotated[List[RadioBandOptions], BeforeValidator(_str_to_list)] = None
    spectrum_radios: Annotated[List[RadioBandOptions], BeforeValidator(_str_to_list)] = None
    flex_dual_exclude: Optional[RadioBandOptions] = None
    dynamic_ant_mode: Optional[DynamicAntMode] = Field(None, alias=AliasChoices("antenna_width", "dynamic_ant_mode"))
    uplink_vlan: Optional[int] = Field(None, alias=AliasChoices("uplink_vlan", "tagged_uplink_vlan"))
    gps_altitude: Optional[float] = None
    boot_partition: Annotated[int, {"min": 0, "max": 1}] = None

    def __str__(self):
        console = Console(force_terminal=False, emoji=False)
        with console.capture() as cap:
            console.print(self.__rich__())
        return cap.get()

    def __rich__(self):
        iden = f"[bright_green]{self.serial}[/]"
        items = "|".join(
            [
                f"{field}: {getattr(self, field) if not isinstance(getattr(self, field), list) else ','.join(getattr(self, field))}"
                for field in self.model_fields_set
                if field != "serial" and getattr(self, field) is not None
            ]
        )
        reboot_msg = "\u267b  " if self.ip else ""  # \u267b :recycle: ♻
        return f"{reboot_msg}{iden}|{items}"

    @model_validator(mode="after")
    def validate_radio_modes(self) -> Self:
        radios = ["2.4", "5", "6"]
        enable_radios = self.enable_radios or []
        disable_radios = self.disable_radios or []
        access_radios = self.access_radios or []
        monitor_radios = self.monitor_radios or []
        spectrum_radios = self.spectrum_radios or []
        checks = [
            {"values": [*disable_radios, *enable_radios], "msg": "radio set to be both enabled and disabled. Which makes no sense."},
            {"values": [*access_radios, *monitor_radios, *spectrum_radios], "msg": "radio defined multiple modes (access, monitor, spectrum)."},
        ]
        for c in checks:
            for r in radios:
                if c["values"].count(r) > 1:
                    ap_iden = self.serial if not self.hostname else f"{self.hostname} ({self.serial})"
                    raise ValueError(f"Invalid import data for {ap_iden},  {r}Ghz {c['msg']}")

        return self

    @model_validator(mode="after")
    def validate_ip_fields(self) -> Self:
        ap_iden = self.serial if not self.hostname else f"{self.hostname} ({self.serial})"
        if self.ip and self.ip.lower() == "dhcp":
            if any([self.mask, self.gateway]):
                raise ValueError(f"Invalid import data for {ap_iden}, mask and gateway are not expected if ip is being set to dhcp")

            # reset static IP values to default (for DHCP)  This is the default so only necessary when changing an AP that previously had a static IP
            self.ip = self.mask = self.gateway = "0.0.0.0"
            # Unsure if static DNS/domain can be configured with dynamic IP
            self.dns = self.dns or ["0.0.0.0"]
            self.domain = self.domain or ""

        elif any([self.ip, self.mask, self.gateway]) and not all([self.ip, self.mask, self.gateway, self.dns]):  # unsure if dns by itself is valid.
            raise ValueError(f"Invalid import data for {ap_iden},  if any of ip, mask, gateway are provided all of ip, mask, gateway, and dns must be provided")

        return self

    @staticmethod
    def _parse_disable_radio_values(enable_radios: None | list, disable_radios: None | list) -> tuple:
        if not disable_radios and not enable_radios:
            return None, None, None

        radio_24_disable = None if not enable_radios or "2.4" not in enable_radios else False
        radio_5_disable = None if not enable_radios or "5" not in enable_radios else False
        radio_6_disable = None if not enable_radios or "6" not in enable_radios else False

        if disable_radios:
            if radio_24_disable is None and "2.4" in disable_radios:
                radio_24_disable = True
            if radio_5_disable is None and "5" in disable_radios:
                radio_5_disable = True
            if radio_6_disable is None and "6" in disable_radios:
                radio_6_disable = True

        return radio_24_disable, radio_5_disable, radio_6_disable

    @staticmethod
    def _parse_radio_mode_values(
        access_radios: None | list,
        monitor_radios: None | list,
        spectrum_radios: None | list,
    ) -> tuple:
        radio_24_mode, radio_5_mode, radio_6_mode = None, None, None
        modes = ["access", "monitor", "spectrum"]
        for mode, radios in zip(modes, [access_radios, monitor_radios, spectrum_radios]):
            if radios is None:
                continue
            if radio_24_mode is None:
                radio_24_mode = None if "2.4" not in radios else mode
            if radio_5_mode is None:
                radio_5_mode = None if "5" not in radios else mode
            if radio_6_mode is None:
                radio_6_mode = None if "6" not in radios else mode

        return radio_24_mode, radio_5_mode, radio_6_mode

    @property
    def api_params(self):
        radios_24_diable, radio_5_disable, radio_6_disable = self._parse_disable_radio_values(self.enable_radios, self.disable_radios)
        radio_24_mode, radio_5_mode, radio_6_mode = self._parse_radio_mode_values(self.access_radios, self.monitor_radios, self.spectrum_radios)
        kwargs = {
            **{k: v for k, v in self.model_dump().items() if k not in ["gps_altitude"] and not k.endswith("_radios")},
            **{
                "radio_24_disable": radios_24_diable,
                "radio_5_disable": radio_5_disable,
                "radio_6_disable": radio_6_disable,
                "radio_24_mode": radio_24_mode,
                "radio_5_mode": radio_5_mode,
                "radio_6_mode": radio_6_mode,
            },
        }

        return kwargs


class APUpdates(RootModel):
    root: List[APUpdate]

    def __init__(self, data: List[dict]) -> None:
        super().__init__([APUpdate(**ap) for ap in data])

    def __iter__(self):
        return iter(self.root)

    def __getitem__(self, item):
        return self.root[item]

    def __len__(self) -> int:
        return len(self.root)