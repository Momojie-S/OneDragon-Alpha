"""FastAPI application for OneDragon Alpha server."""
import os
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from one_dragon_alpha.server.chat.router import router as chat_router
from one_dragon_alpha.server.context import OneDragonAlphaContext
from one_dragon_agent.core.model.router import router as model_config_router
from one_dragon_agent.core.model.qwen.oauth_router import router as qwen_oauth_router


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

# 配置 CORS 允许的源
allow_origins = [
    "http://localhost:21002",
    "http://127.0.0.1:21002",
    "http://localhost:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:5174",
    "http://momojie.online:21002",
    "http://momojie.online",
    "https://momojie.online",
    "http://api.momojie.online",
    "https://api.momojie.online",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,  # 允许跨域请求携带认证信息
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(chat_router)
app.include_router(model_config_router)
app.include_router(qwen_oauth_router)


if __name__ == "__main__":
    port = int(os.getenv("API_PORT", "21003"))
    uvicorn.run(app, port=port)