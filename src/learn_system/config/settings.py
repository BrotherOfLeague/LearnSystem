"""应用配置管理

基于 Pydantic Settings 和 python-dotenv 实现配置管理。
"""

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    """应用基础配置"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="",
        case_sensitive=False,
    )

    # 应用环境
    app_env: str = Field(default="dev", description="应用环境：dev, test, prod")

    # Python 文档版本
    python_docs_version: str = Field(default="3.15", description="Python 文档版本")

    # 数据目录
    docs_source_dir: Path = Field(default=Path("./data/raw"), description="原始文档目录")
    processed_dir: Path = Field(default=Path("./data/processed"), description="处理后数据目录")
    chroma_dir: Path = Field(default=Path("./storage/chroma"), description="Chroma 向量存储目录")

    # Embedding 配置
    embedding_provider: str = Field(default="local", description="Embedding 提供商：local, openai")
    embedding_model: str = Field(default="BAAI/bge-m3", description="Embedding 模型名称")
    embedding_batch_size: int = Field(default=16, description="Embedding 批处理大小")

    # LLM 配置
    llm_provider: str = Field(default="openai", description="LLM 提供商：openai, deepseek")
    llm_api_key: str | None = Field(default=None, description="LLM API Key")
    llm_base_url: str | None = Field(default=None, description="LLM API Base URL")
    llm_model: str = Field(default="gpt-4o-mini", description="LLM 模型名称")
    llm_temperature: float = Field(default=0.7, description="LLM 采样温度")

    # 检索配置
    retrieval_top_k: int = Field(default=8, description="检索返回结果数量")

    # 分块配置
    chunk_target_size: int = Field(default=800, description="目标分块大小（字符数）")
    chunk_overlap: int = Field(default=120, description="分块重叠大小（字符数）")

    # 日志配置
    log_level: str = Field(default="INFO", description="日志级别")


def get_settings() -> AppSettings:
    """获取应用配置单例"""
    return AppSettings()


# 全局配置实例
settings = get_settings()
