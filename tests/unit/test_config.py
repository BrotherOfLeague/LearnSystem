"""配置模块测试"""

import tempfile
from pathlib import Path

import pytest

from learn_system.config.settings import AppSettings, get_settings


class TestAppSettings:
    """AppSettings 测试类"""

    def test_default_values(self):
        """测试默认值"""
        settings = AppSettings()

        assert settings.app_env == "dev"
        assert settings.python_docs_version == "3.12"
        assert settings.embedding_provider == "local"
        assert settings.llm_provider == "openai"
        assert settings.retrieval_top_k == 8
        assert settings.chunk_target_size == 800
        assert settings.chunk_overlap == 120

    def test_env_file_loading(self):
        """测试环境变量文件加载"""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = Path(tmpdir) / ".env"
            env_file.write_text("""
APP_ENV=test
PYTHON_DOCS_VERSION=3.11
RETRIEVAL_TOP_K=5
""")

            settings = AppSettings(_env_file=str(env_file))

            assert settings.app_env == "test"
            assert settings.python_docs_version == "3.11"
            assert settings.retrieval_top_k == 5

    def test_env_var_override(self):
        """测试环境变量覆盖"""
        with pytest.MonkeyPatch().context() as m:
            m.setenv("APP_ENV", "prod")
            m.setenv("RETRIEVAL_TOP_K", "10")

            settings = AppSettings()

            assert settings.app_env == "prod"
            assert settings.retrieval_top_k == 10

    def test_path_expansion(self):
        """测试路径展开"""
        settings = AppSettings(
            docs_source_dir="./data/raw",
            processed_dir="./data/processed",
            chroma_dir="./storage/chroma",
        )

        assert settings.docs_source_dir == Path("./data/raw")
        assert settings.processed_dir == Path("./data/processed")
        assert settings.chroma_dir == Path("./storage/chroma")


class TestGetSettings:
    """get_settings 测试类"""

    def test_returns_app_settings(self):
        """测试返回 AppSettings 实例"""
        settings = get_settings()
        assert isinstance(settings, AppSettings)
