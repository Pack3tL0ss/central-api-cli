from typing import Union, List
from pydantic import BaseModel

# fields from Response.output after cleaner
class Inventory(BaseModel):
    sku: str
    type: str
    mac: str
    model: str
    serial: str
    services: Union[List[str], str]
