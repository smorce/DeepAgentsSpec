from fastapi import FastAPI
from fastapi.responses import JSONResponse
from src.routes import minirag

app = FastAPI(title="API Gateway", version="0.1.0")

app.include_router(minirag.router)

@app.get("/health")
async def health_check():
    return JSONResponse(content={"status": "OK"}, status_code=200)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
