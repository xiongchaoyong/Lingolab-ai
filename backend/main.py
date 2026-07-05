"""FastAPI 应用入口"""

import os
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# HuggingFace 镜像（在导入模型前设置）
if "HF_ENDPOINT" not in os.environ:
    os.environ["HF_ENDPOINT"] = os.getenv("HF_ENDPOINT", "https://hf-mirror.com")

logger = logging.getLogger("uvicorn")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期：启动时预加载模型，关闭时释放资源"""
    logger.info("正在启动服务...")

    # 预加载知识图谱（NetworkX 内存图）
    try:
        from app.core.database import SessionLocal
        from app.services.knowledge_graph import kg_service
        db = SessionLocal()
        kg_service.load_from_db(db)
        db.close()
        logger.info("知识图谱加载完成")
    except Exception as e:
        logger.warning(f"知识图谱加载失败: {e}")

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

# 全局异常处理 — 确保 500 错误也返回 CORS 头
from fastapi.responses import JSONResponse
from fastapi.requests import Request

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"未捕获异常: {type(exc).__name__}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": f"服务器内部错误: {str(exc)}"},
        headers={"Access-Control-Allow-Origin": "*"},
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
from app.api.voice_chat import router as voice_chat_router
from app.api.auth import router as auth_router
from app.api.assessment import router as assessment_router
from app.api.learning_path import router as learning_path_router
from app.api.recommendation import router as recommendation_router
from app.api.grammar import router as grammar_router
from app.api.admin import router as admin_router
from app.api.student import router as student_router
from app.api.community import router as community_router
from app.api.gamification import router as gamification_router
from app.api.progress import router as progress_router
from app.api.prediction import router as prediction_router
from app.api.help import router as help_router
from app.api.feedback import router as feedback_router

app.include_router(pronunciation_router, prefix="/api/pronunciation", tags=["发音评测"])
app.include_router(conversation_router, prefix="/api/conversation", tags=["语音对话"])
app.include_router(roleplay_router, prefix="/api/roleplay", tags=["角色扮演"])
app.include_router(voice_chat_router, prefix="/api/voice-chat", tags=["语音对话"])
app.include_router(auth_router, prefix="/api/auth", tags=["用户认证"])
app.include_router(assessment_router, prefix="/api/assessment", tags=["水平测评"])
app.include_router(learning_path_router, prefix="/api/learning-path", tags=["学习路径"])
app.include_router(recommendation_router, prefix="/api/recommendations", tags=["资料推荐"])
app.include_router(grammar_router, prefix="/api/grammar", tags=["语法纠错"])
app.include_router(admin_router, prefix="/api/admin", tags=["后台管理"])
app.include_router(student_router, prefix="/api/student", tags=["学生端"])
app.include_router(community_router, prefix="/api/community", tags=["社区服务"])
app.include_router(gamification_router, prefix="/api/gamification", tags=["游戏化闯关"])
app.include_router(progress_router, prefix="/api/progress", tags=["学习进度"])
app.include_router(prediction_router, prefix="/api", tags=["学习预测"])
app.include_router(help_router, prefix="/api/help", tags=["智能客服"])
app.include_router(feedback_router, prefix="/api/feedback", tags=["用户反馈"])

# 静态文件服务 — 上传的头像等资源
app.mount("/static", StaticFiles(directory="uploads"), name="static")
