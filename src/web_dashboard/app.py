"""FastAPI backend для веб-дашборда."""

from fastapi import FastAPI


app = FastAPI(title="DMarket Bot Dashboard API", version="1.0.0")


@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint."""
    return {"message": "DMarket Bot Dashboard API", "version": "1.0.0"}


@app.get("/api/v1/health")
async def health() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok"}
