"""CLI 界面"""

import logging

from learn_system.config.settings import settings
from learn_system.embedding.local import LocalEmbeddingProvider
from learn_system.llm.openai_client import OpenAIClient
from learn_system.retriever.chroma_store import ChromaVectorStore
from learn_system.retriever.rag_engine import RAGEngine
from learn_system.retriever.retriever import Retriever

logger = logging.getLogger(__name__)


class CLI:
    """命令行界面"""

    def __init__(self):
        self.retriever: Retriever | None = None
        self.rag_engine: RAGEngine | None = None
        self._initialized = False

    def initialize(self) -> bool:
        """初始化组件"""
        try:
            if not settings.llm_api_key:
                logger.error("未配置 LLM_API_KEY，请在 .env 中设置")
                return False

            # 初始化 Embedding
            embedding_provider = LocalEmbeddingProvider(
                model_name=settings.embedding_model,
            )

            # 初始化 Vector Store
            vector_store = ChromaVectorStore(
                persist_dir=settings.chroma_dir,
            )

            # 初始化 Retriever
            self.retriever = Retriever(
                vector_store=vector_store,
                embedding_provider=embedding_provider,
                top_k=settings.retrieval_top_k,
            )

            # 初始化 LLM
            llm_client = OpenAIClient(
                api_key=settings.llm_api_key,
                base_url=settings.llm_base_url,
                model=settings.llm_model,
                temperature=settings.llm_temperature,
            )

            # 初始化 RAG Engine
            self.rag_engine = RAGEngine(
                retriever=self.retriever,
                llm_client=llm_client,
            )

            self._initialized = True
            return True

        except Exception as err:
            logger.error(f"初始化失败: {err}")
            return False

    def run(self) -> None:
        """运行交互式问答"""
        if not self._initialized:
            if not self.initialize():
                print("初始化失败，请检查 .env 配置（需要 LLM_API_KEY）")
                return

        print("=" * 60)
        print("Python 官方文档问答助手")
        print("输入 'quit' 或 'exit' 退出")
        print("=" * 60)
        print()

        while True:
            try:
                question = input("请输入您的问题: ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\n再见！")
                break

            if not question:
                continue

            if question.lower() in ["quit", "exit", "q", "退出"]:
                print("再见！")
                break

            if question.lower() in ["help", "帮助"]:
                self._show_help()
                continue

            if question.lower() in ["stats", "统计"]:
                self._show_stats()
                continue

            try:
                response = self.rag_engine.ask(question)
                print()
                print(response.format())
                print()
            except Exception as err:
                logger.error(f"处理问题失败: {err}")
                print(f"抱歉，处理您的问题时出现错误: {err}")

    def _show_help(self) -> None:
        """显示帮助"""
        help_text = """
可用命令：
  - 直接输入问题进行问答
  - stats    - 显示索引统计信息
  - help     - 显示此帮助信息
  - quit/exit - 退出程序
        """
        print(help_text)

    def _show_stats(self) -> None:
        """显示统计信息"""
        if self.retriever:
            count = self.retriever.count()
            if count == 0:
                print("索引为空，请先运行构建索引命令")
            else:
                print(f"索引中的文档块数量: {count}")
        else:
            print("尚未初始化")


def main() -> None:
    """主入口"""
    logging.basicConfig(level=getattr(logging, settings.log_level.upper(), logging.INFO))
    CLI().run()


if __name__ == "__main__":
    main()
