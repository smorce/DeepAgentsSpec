from fastapi import FastAPI
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
import os
from src.routes import minirag
from src.minirag.postgres_service import PostgresMiniRAGService

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting up API Gateway...")

    # Initialize MiniRAG service if strictly Postgres (optional explicit init)
    # The get_service() dependency lazily inits, but for Postgres we might want strict check.
    # For now, we rely on lazy init or manual call here.
    service = await minirag.get_service()
    if isinstance(service, PostgresMiniRAGService):
        logger.info("Initializing Postgres Database connection and schema...")
        await service.connect()
        await service.init_db()

    yield

    # Shutdown
    logger.info("Shutting down API Gateway...")
    if isinstance(service, PostgresMiniRAGService):
        logger.info("Closing Postgres connection...")
        await service.disconnect()

app = FastAPI(title="API Gateway", version="0.1.0", lifespan=lifespan)

app.include_router(minirag.router)

@app.get("/health")
async def health_check():
    return JSONResponse(content={"status": "OK"}, status_code=200)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
