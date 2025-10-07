from typing import List

from pydantic import BaseModel, Field


class ExplainDelayRequest(BaseModel):
    order_id: str
    note: str = Field(default="")


class ExplainDelayResponse(BaseModel):
    order_id: str
    label: str
    confidence: float
    version: str
    top3: List[dict]
