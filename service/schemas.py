from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class Delivery(BaseModel):
    order_id: str
    yard_id: str
    route_id: Optional[str] = None
    promised_eta: datetime
    actual_eta: Optional[datetime] = None
    status: str  # scheduled | enroute | delivered | delayed | canceled


class Deliveries(BaseModel):
    deliveries: List[Delivery]
