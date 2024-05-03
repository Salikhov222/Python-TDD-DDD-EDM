import uvicorn
from fastapi import FastAPI

from src.allocation.entrypoints.routes.allocate import allocate_router
from src.allocation.entrypoints.routes.batches import batches_router

app = FastAPI()

# Register routes
app.include_router(allocate_router, prefix="/allocate")
app.include_router(batches_router, prefix="/batches")

@app.get("/")
async def home():
    return {
        "message": "Architecture Patterns with Python"
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)