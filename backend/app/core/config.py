"""应用配置 — 基于 Pydantic Settings 加载环境变量"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # 数据库
    database_url: str = "mysql+pymysql://root:@localhost:3306/english_training_dev"

    # AI（阿里百炼 DashScope）
    bailian_api_key: str = ""
    hf_endpoint: str = "https://hf-mirror.com"

    # JWT
    jwt_secret_key: str = "dev-secret"

    # 豆包 TTS（可选）
    doubao_app_id: str = ""
    doubao_access_key: str = ""

    # 发音评测
    pronunciation_device: str = "auto"  # auto | cpu | mps

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
