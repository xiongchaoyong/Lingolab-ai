"""FastAPI 应用入口"""

import os
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# HuggingFace 镜像（在导入模型前设置）
if "HF_ENDPOINT" not in os.environ:
    os.environ["HF_ENDPOINT"] = os.getenv("HF_ENDPOINT", "https://hf-mirror.com")

logger = logging.getLogger("uvicorn")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期：启动时预加载模型，关闭时释放资源"""
    logger.info("正在启动服务...")

    # 预加载发音评测模型（wav2vec2 + G2P）
    try:
        from app.services.pronunciation import get_pronunciation_service
        service = get_pronunciation_service()
        logger.info("发音评测模型加载完成")
    except Exception as e:
        logger.warning(f"发音评测模型加载失败（可启动后重试）: {e}")

    yield

    logger.info("服务关闭")


app = FastAPI(
    title="Lingolab-ai 英语口语训练系统",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS — 开发阶段允许所有来源
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health_check():
    """健康检查"""
    return {"status": "ok", "version": "0.1.0"}


# 注册路由
from app.api.pronunciation import router as pronunciation_router
from app.api.conversation import router as conversation_router
from app.api.roleplay import router as roleplay_router

app.include_router(pronunciation_router, prefix="/api/pronunciation", tags=["发音评测"])
app.include_router(conversation_router, prefix="/api/conversation", tags=["语音对话"])
app.include_router(roleplay_router, prefix="/api/roleplay", tags=["角色扮演"])
