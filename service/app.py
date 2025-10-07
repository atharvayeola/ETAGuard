from ml_server import app

__all__ = ["app"]


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("ml_server:app", host="0.0.0.0", port=8000, reload=True)
