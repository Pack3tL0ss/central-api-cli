from pydantic import BaseModel, RootModel, ConfigDict, Field, AliasChoices


class Details(BaseModel):
    model_config = ConfigDict(extra="allow")
    # __base_url: str
    # _rule_number: str
    params: list[str]
    group: str
    group_name: str
    labels: str
    serial: str
    time: str


# Used to format alert response from API to look like the payload of webhook
class Alert(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: str
    cid: str = Field(alias=AliasChoices("cid", "customer_id"))
    nid: int
    alert_type: str = Field(alias=AliasChoices("alert_type", "type"))
    setting_id: str
    device_id: str
    description: str
    state: str
    severity: str
    timestamp: int
    details: Details
    # acknowledged: bool
    # created_timestamp: float
    # group_name: str
    # labels: list


class Alerts(RootModel):
    root: list[Alert]

    def __init__(self, data: list[dict]) -> None:
        super().__init__([Alert(**a) for a in data])

    def __iter__(self):
        return iter(self.root)

    def __getitem__(self, item):
        return self.root[item]

    def __len__(self) -> int:
        return len(self.root)

