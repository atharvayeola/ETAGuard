import os
import datetime as dt
from typing import List, Dict

import httpx

AUTH_COOKIE = os.environ.get("MYBLDR_AUTH_COOKIE", "")
SERVICE_SOURCE_URL = os.environ.get("MYBLDR_SOURCE_URL")


async def fetch_raw_async() -> List[Dict]:
    """Fetch raw delivery data from myBLDR or another upstream source.

    This stub supports two modes:
    * If `MYBLDR_SOURCE_URL` is set, perform an authenticated GET request.
    * Otherwise return a hard-coded sample payload for local testing.
    """
    if SERVICE_SOURCE_URL:
        async with httpx.AsyncClient(timeout=10.0) as client:
            headers = {"Cookie": AUTH_COOKIE} if AUTH_COOKIE else {}
            response = await client.get(SERVICE_SOURCE_URL, headers=headers)
            response.raise_for_status()
            data = response.json()
            if isinstance(data, dict) and "deliveries" in data:
                return data["deliveries"]
            return data

    # Default sample for smoke-testing without an upstream API.
    now = dt.datetime.now(dt.timezone.utc)
    promised = now - dt.timedelta(minutes=40)
    actual = now
    return [
        {
            "order_id": "B12345",
            "yard_id": "SD01",
            "route_id": "R-9",
            "promised_eta": promised.isoformat(),
            "actual_eta": actual.isoformat(),
            "status": "delivered",
            "note": "Gate was locked; driver waiting for access code.",
        }
    ]


def normalize(raw: List[Dict]) -> List[Dict]:
    """Normalize upstream payloads into the ETAguard contract."""
    deliveries = []
    for record in raw:
        deliveries.append(
            {
                "order_id": record["order_id"],
                "yard_id": record["yard_id"],
                "route_id": record.get("route_id"),
                "promised_eta": record["promised_eta"],
                "actual_eta": record.get("actual_eta"),
                "status": record["status"].lower(),
                "note": record.get("note"),
            }
        )
    return deliveries
