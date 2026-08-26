"""匹配准确度评估：验证语义 embedding 的区分度。

用法：
    cd backend
    python -m eval.matching_eval
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.embeddings import embed_hash_fallback, embed_text


CASES = [
    ("高度匹配", "熟悉 Python 后端开发，熟练使用 FastAPI", "精通 Python 服务端编程，有 FastAPI 项目经验"),
    ("同义改写", "精通 K8s 容器编排", "熟悉 Kubernetes 集群管理"),
    ("领域相关", "熟悉 LangChain 与 RAG", "了解大模型应用与 Agent"),
    ("跨行", "精通 Python 后端开发", "擅长前端 Vue 页面开发"),
]


def _cosine(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def main():
    semantic = embed_text("test") is not None
    print(f"真语义 embedding 可用: {semantic}")
    print("-" * 50)

    for label, a, b in CASES:
        va = embed_text(a) if semantic else None
        vb = embed_text(b) if semantic else None
        if va is None:
            va = embed_hash_fallback(a)
        if vb is None:
            vb = embed_hash_fallback(b)
        sim = _cosine(va, vb)
        print(f"{label}: 相似度 {sim:.4f}")

    print("-" * 50)
    print("验收参考：高度匹配/同义改写应明显高于跨行；真语义模型下同义改写应接近 0.8+")


if __name__ == "__main__":
    main()
