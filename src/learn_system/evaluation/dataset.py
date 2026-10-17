"""评估数据集"""

from dataclasses import dataclass


@dataclass
class EvaluationQuestion:
    """评估问题"""

    question: str
    expected_urls: list[str]
    keywords: list[str] | None = None
    category: str = "general"
    difficulty: str = "medium"

    def __post_init__(self):
        if self.keywords is None:
            self.keywords = []


# Python 官方文档评估集（30 个问题）
EVALUATION_DATASET: list[EvaluationQuestion] = [
    EvaluationQuestion(
        question="Python 中的生成器是什么？",
        expected_urls=["https://docs.python.org/3.15/tutorial/classes.html#generators"],
        keywords=["generator", "yield"],
        category="concept",
        difficulty="easy",
    ),
    EvaluationQuestion(
        question="什么是装饰器？",
        expected_urls=["https://docs.python.org/3.15/tutorial/classes.html#decorator"],
        keywords=["decorator"],
        category="concept",
        difficulty="medium",
    ),
    EvaluationQuestion(
        question="enumerate 函数如何使用？",
        expected_urls=["https://docs.python.org/3.15/builtins/functions.html#enumerate"],
        keywords=["enumerate"],
        category="api",
        difficulty="easy",
    ),
    EvaluationQuestion(
        question="map 函数的作用是什么？",
        expected_urls=["https://docs.python.org/3.15/builtins/functions.html#map"],
        keywords=["map"],
        category="api",
        difficulty="easy",
    ),
    EvaluationQuestion(
        question="filter 函数如何使用？",
        expected_urls=["https://docs.python.org/3.15/builtins/functions.html#filter"],
        keywords=["filter"],
        category="api",
        difficulty="easy",
    ),
    EvaluationQuestion(
        question="zip 函数的作用是什么？",
        expected_urls=["https://docs.python.org/3.15/builtins/functions.html#zip"],
        keywords=["zip"],
        category="api",
        difficulty="easy",
    ),
    EvaluationQuestion(
        question="list comprehension 如何使用？",
        expected_urls=[
            "https://docs.python.org/3.15/tutorial/datastructures.html#list-comprehensions"
        ],
        keywords=["list comprehension"],
        category="api",
        difficulty="easy",
    ),
    EvaluationQuestion(
        question="sorted 函数如何使用？",
        expected_urls=["https://docs.python.org/3.15/builtins/functions.html#sorted"],
        keywords=["sorted"],
        category="api",
        difficulty="easy",
    ),
    EvaluationQuestion(
        question="如何读取 JSON 文件？",
        expected_urls=["https://docs.python.org/3.15/library/json.html#json.load"],
        keywords=["json"],
        category="stdlib",
        difficulty="easy",
    ),
    EvaluationQuestion(
        question="如何处理日期和时间？",
        expected_urls=["https://docs.python.org/3.15/library/datetime.html"],
        keywords=["datetime"],
        category="stdlib",
        difficulty="medium",
    ),
    EvaluationQuestion(
        question="os.path 模块有哪些常用函数？",
        expected_urls=["https://docs.python.org/3.15/library/os.path.html"],
        keywords=["os.path"],
        category="stdlib",
        difficulty="easy",
    ),
    EvaluationQuestion(
        question="pathlib 如何处理文件路径？",
        expected_urls=["https://docs.python.org/3.15/library/pathlib.html"],
        keywords=["pathlib"],
        category="stdlib",
        difficulty="medium",
    ),
    EvaluationQuestion(
        question="logging 模块如何配置？",
        expected_urls=["https://docs.python.org/3.15/library/logging.html"],
        keywords=["logging"],
        category="stdlib",
        difficulty="medium",
    ),
    EvaluationQuestion(
        question="argparse 模块如何使用？",
        expected_urls=["https://docs.python.org/3.15/library/argparse.html"],
        keywords=["argparse"],
        category="stdlib",
        difficulty="medium",
    ),
    EvaluationQuestion(
        question="Python 中如何处理异常？",
        expected_urls=["https://docs.python.org/3.15/tutorial/errors.html"],
        keywords=["exception"],
        category="stdlib",
        difficulty="easy",
    ),
    EvaluationQuestion(
        question="defaultdict 如何使用？",
        expected_urls=["https://docs.python.org/3.15/library/collections.html#defaultdict"],
        keywords=["defaultdict"],
        category="stdlib",
        difficulty="medium",
    ),
    EvaluationQuestion(
        question="如何创建和读取 CSV 文件？",
        expected_urls=["https://docs.python.org/3.15/library/csv.html"],
        keywords=["csv"],
        category="stdlib",
        difficulty="easy",
    ),
    EvaluationQuestion(
        question="lru_cache 的作用是什么？",
        expected_urls=["https://docs.python.org/3.15/library/functools.html#functools.lru_cache"],
        keywords=["lru_cache"],
        category="stdlib",
        difficulty="medium",
    ),
    EvaluationQuestion(
        question="如何实现深拷贝和浅拷贝？",
        expected_urls=["https://docs.python.org/3.15/library/copy.html"],
        keywords=["copy", "deepcopy"],
        category="example",
        difficulty="medium",
    ),
    EvaluationQuestion(
        question="正则表达式如何使用？",
        expected_urls=["https://docs.python.org/3.15/library/re.html"],
        keywords=["re", "regex"],
        category="example",
        difficulty="medium",
    ),
    EvaluationQuestion(
        question="Python 中如何格式化字符串？",
        expected_urls=["https://docs.python.org/3.15/library/string.html#formatstrings"],
        keywords=["format"],
        category="example",
        difficulty="easy",
    ),
    EvaluationQuestion(
        question="如何用 hashlib 计算字符串的哈希？",
        expected_urls=["https://docs.python.org/3.15/library/hashlib.html"],
        keywords=["hashlib"],
        category="example",
        difficulty="easy",
    ),
    EvaluationQuestion(
        question="Python 中 None、False、0 的布尔值是什么？",
        expected_urls=["https://docs.python.org/3.15/builtins/stdtypes.html#truth-value-testing"],
        keywords=["truth value"],
        category="boundary",
        difficulty="medium",
    ),
    EvaluationQuestion(
        question="可变对象和不可变对象的区别？",
        expected_urls=[
            "https://docs.python.org/3.15/builtins/stdtypes.html#immutable-sequence-types"
        ],
        keywords=["immutable", "mutable"],
        category="boundary",
        difficulty="medium",
    ),
    EvaluationQuestion(
        question="*args 和 **kwargs 是什么？",
        expected_urls=[
            "https://docs.python.org/3.15/tutorial/controlflow.html#unpacking-argument-lists"
        ],
        keywords=["*args", "**kwargs"],
        category="boundary",
        difficulty="medium",
    ),
    EvaluationQuestion(
        question="如何实现属性（Property）？",
        expected_urls=["https://docs.python.org/3.15/builtins/functions.html#property"],
        keywords=["property"],
        category="advanced",
        difficulty="medium",
    ),
    EvaluationQuestion(
        question="类型注解如何使用？",
        expected_urls=["https://docs.python.org/3.15/library/typing.html"],
        keywords=["type hint", "typing"],
        category="advanced",
        difficulty="medium",
    ),
    EvaluationQuestion(
        question="dataclass 是什么？",
        expected_urls=["https://docs.python.org/3.15/library/dataclasses.html"],
        keywords=["dataclass"],
        category="advanced",
        difficulty="easy",
    ),
    EvaluationQuestion(
        question="上下文管理器如何使用？",
        expected_urls=["https://docs.python.org/3.15/reference/compound_stmts.html#with"],
        keywords=["context manager", "with"],
        category="concept",
        difficulty="medium",
    ),
    EvaluationQuestion(
        question="isinstance 和 type 的区别？",
        expected_urls=["https://docs.python.org/3.15/builtins/functions.html#isinstance"],
        keywords=["isinstance", "type"],
        category="api",
        difficulty="medium",
    ),
]


def get_dataset() -> list[EvaluationQuestion]:
    return EVALUATION_DATASET


def get_dataset_by_category(category: str) -> list[EvaluationQuestion]:
    return [q for q in EVALUATION_DATASET if q.category == category]


def get_dataset_stats() -> dict:
    categories: dict[str, int] = {}
    difficulties: dict[str, int] = {}

    for q in EVALUATION_DATASET:
        categories[q.category] = categories.get(q.category, 0) + 1
        difficulties[q.difficulty] = difficulties.get(q.difficulty, 0) + 1

    return {
        "total": len(EVALUATION_DATASET),
        "categories": categories,
        "difficulties": difficulties,
    }
