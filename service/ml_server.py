from fastapi import FastAPI

try:  # pragma: no cover - support running as module or package
    from .client import fetch_raw_async, normalize
    from .nlp_text_triage import predict_note
    from .schemas import Deliveries
    from .schemas_text import ExplainDelayRequest, ExplainDelayResponse
except ImportError:  # pragma: no cover
    from client import fetch_raw_async, normalize
    from nlp_text_triage import predict_note
    from schemas import Deliveries
    from schemas_text import ExplainDelayRequest, ExplainDelayResponse

app = FastAPI(title="ETAguard Proxy", version="0.2.0")


@app.get("/deliveries", response_model=Deliveries)
async def deliveries() -> Deliveries:
    raw = await fetch_raw_async()
    return {"deliveries": normalize(raw)}


@app.get("/health")
async def health() -> dict:
    return {"ok": True}


@app.post("/explain_delay", response_model=ExplainDelayResponse)
def explain_delay(request: ExplainDelayRequest) -> ExplainDelayResponse:
    prediction = predict_note(request.note or "")
    return ExplainDelayResponse(
        order_id=request.order_id,
        label=prediction["label"],
        confidence=prediction["confidence"],
        version=prediction["version"],
        top3=prediction["top3"],
    )


@app.get("/ml_health")
def ml_health() -> dict:
    return {"ok": True}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("ml_server:app", host="0.0.0.0", port=8000, reload=True)
