"""FastAPI application for OneDragon Alpha server."""
import os
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from one_dragon_alpha.server.chat.router import router as chat_router
from one_dragon_alpha.server.context import OneDragonAlphaContext


@asynccontextmanager
async def lifespan(api: FastAPI):
    """Application lifespan events."""
    # Initialize global context on startup
    OneDragonAlphaContext.initialize()
    yield
    # Cleanup on shutdown
    OneDragonAlphaContext.reset()


app = FastAPI(
    title="OneDragon Alpha API",
    description="OneDragon Alpha backend server API",
    version="0.1.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if os.getenv("ODA_ENVIRONMENT") == "DEV" else ["https://api.onedragonalpha.com"],
    allow_credentials=True,  # 允许跨域请求携带认证信息
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(chat_router)


if __name__ == "__main__":
    uvicorn.run(app, port=8888)