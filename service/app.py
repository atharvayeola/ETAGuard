from fastapi import FastAPI

from schemas import Deliveries
from client import fetch_raw_async, normalize

app = FastAPI(title="ETAguard Proxy")


@app.get("/deliveries", response_model=Deliveries)
async def deliveries():
    raw = await fetch_raw_async()
    return {"deliveries": normalize(raw)}


@app.get("/health")
async def health():
    return {"ok": True}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
