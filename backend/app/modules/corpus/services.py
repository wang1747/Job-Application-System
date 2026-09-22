"""语料库服务：贡献入库 + 语义检索（RAG 的检索层）。

设计对齐 deploy/PLAN.md 的「语料库建设」：
  - 整篇 embedding（不切片，OfferFlow 语料是短文档：简历 800 字 / JD 千字 / 面经）
  - 语料写入 corpus_items（PG，SQLAlchemy）+ 向量存 ChromaDB（corpus_embeddings）
  - retrieve_similar 检索最相似语料，喂给 LLM 做参考
  - 分类：复用 skill_keywords 的真实 JD 词频库做方向标签；技能词打 tags
"""
from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from app.models.corpus import CorpusItem
from app.core.vector_store import get_vector_store, get_or_create_collection
from app.core.embeddings import embed_text, embed_hash_fallback
from app.core.skill_keywords import keyword_set
from app.core.hybrid import bm25_search, rrf_fuse

_CORPUS_COLLECTION = "corpus_embeddings"


# ============ 分类 ============

def classify_direction(text: str) -> Optional[str]:
    """用 19 大类求职方向关键词表（salary_benchmark）做粗分类，返回中文方向标签。

    0 命中返回 None（方向可空，检索时不强制过滤）。
    """
    from app.core.salary_benchmark import _DIRECTION_KEYWORDS, DIRECTION_COEF
    t = (text or "").lower()
    best_key, best_n = None, 0
    for key, kws in _DIRECTION_KEYWORDS:
        n = sum(1 for kw in kws if kw and kw.lower() in t)
        if n > best_n:
            best_key, best_n = key, n
    if not best_key:
        return None
    return DIRECTION_COEF.get(best_key, (0.0, best_key))[1]


def extract_tags(text: str, limit: int = 20) -> List[str]:
    """从文本中提取命中真实 JD 词频库的技能词作为 tags（供过滤/展示）。"""
    kws = keyword_set()
    if not kws:
        return []
    t = (text or "").lower()
    hits = sorted({kw for kw in kws if kw in t})
    return hits[:limit]


# ============ 入库 ============

def _embed(text: str) -> List[float]:
    return embed_text(text) or embed_hash_fallback(text)


def add_corpus_item(
    item_type: str,
    raw_text: str,
    db: Session,
    structured: Optional[dict] = None,
    tags: Optional[List[str]] = None,
    source: str = "user_upload",
    user_id: Optional[str] = None,
    is_public: bool = False,
    auto_tag: bool = True,
) -> CorpusItem:
    """写入一条语料：存 corpus_items（PG）+ 整篇 embedding 存 Chroma。

    embedding 失败不阻断入库（语料仍在，只是暂不可语义检索）。
    """
    direction = classify_direction(raw_text)
    final_tags = list(tags or [])
    if auto_tag:
        final_tags = list(dict.fromkeys(final_tags + extract_tags(raw_text)))

    item = CorpusItem(
        item_type=item_type,
        raw_text=raw_text,
        structured=structured,
        tags=final_tags,
        direction=direction,
        source=source,
        user_id=user_id,
        is_public=is_public,
    )
    db.add(item)
    db.commit()
    db.refresh(item)

    try:
        collection = get_or_create_collection(
            get_vector_store(),
            _CORPUS_COLLECTION,
            metadata={"hnsw:space": "cosine"},
        )
        collection.upsert(
            ids=[item.id],
            embeddings=[_embed(raw_text)],
            documents=[raw_text],
            metadatas=[{
                "item_type": item_type,
                "direction": direction or "",
                "source": source,
            }],
        )
        item.embedding_id = item.id
        db.commit()
    except Exception as e:  # noqa: BLE001
        print(f"[WARN] 语料 embedding 失败（不影响入库）: {e}")

    return item


# ============ 检索 ============

def retrieve_similar(
    query_text: str,
    top_k: int = 5,
    item_type: Optional[str] = None,
    direction: Optional[str] = None,
    db: Optional[Session] = None,
    hybrid: bool = True,
) -> List[Dict]:
    """检索语料库中最相似的 N 条，返回结构化结果（含相似度）。

    默认走「向量 + BM25 混合检索（RRF 融合）」；BM25 关键词召回对技术术语更友好。
    hybrid=False 时回退到纯向量检索。db 传入时从 PG 取 structured 与原文。

    返回 [{id, item_type, raw_text, structured, tags, direction, score}]。
    """
    if not query_text or not query_text.strip():
        return []

    # 召回池：多召回几路，给 RRF 融合留出重排空间
    pool = max(top_k, min(top_k * 5, 60))

    # ---- 1) 向量召回 ----
    vector_hits: List[tuple] = []          # [(id, similarity)]
    docs_by_id: Dict[str, str] = {}
    metas_by_id: Dict[str, dict] = {}
    try:
        collection = get_or_create_collection(
            get_vector_store(),
            _CORPUS_COLLECTION,
            metadata={"hnsw:space": "cosine"},
        )
        where = {}
        if item_type:
            where["item_type"] = item_type
        if direction:
            where["direction"] = direction
        results = collection.query(
            query_embeddings=[_embed(query_text)],
            n_results=pool,
            where=where or None,
            include=["metadatas", "distances", "documents"],
        )
        ids = (results.get("ids") or [[]])[0]
        distances = (results.get("distances") or [[]])[0]
        metadatas = (results.get("metadatas") or [[]])[0]
        documents = (results.get("documents") or [[]])[0]
        for idx, cid in enumerate(ids):
            dist = distances[idx] if idx < len(distances) else 1.0
            vector_hits.append((cid, max(0.0, min(1.0, 1.0 - dist))))
            docs_by_id[cid] = documents[idx] if idx < len(documents) else ""
            metas_by_id[cid] = metadatas[idx] if idx < len(metadatas) else {}
    except Exception as e:  # noqa: BLE001
        print(f"[WARN] 向量检索失败: {e}")

    # ---- 2) BM25 关键词召回 ----
    bm25_hits: List[tuple] = []
    if hybrid and db is not None:
        try:
            bm25_hits = bm25_search(db, query_text, pool, item_type, direction)
        except Exception as e:  # noqa: BLE001
            print(f"[WARN] BM25 检索失败: {e}")

    # ---- 3) RRF 融合 ----
    vec_score = {cid: s for cid, s in vector_hits}
    if bm25_hits:
        fused = rrf_fuse(vector_hits, bm25_hits)
        ranked_ids = [cid for cid, _ in fused[:top_k]]
        # BM25 独有命中的项，给一个随排名递减的分数（0~1 量级）
        rank_score = {cid: round(1.0 / (i + 1), 4) for i, (cid, _) in enumerate(fused[:top_k])}
    else:
        ranked_ids = [cid for cid, _ in vector_hits[:top_k]]
        rank_score = {}

    if not ranked_ids:
        return []

    # ---- 4) 从 PG 取原文/结构化（PG 是 source of truth）----
    items_by_id: Dict[str, CorpusItem] = {}
    if db is not None:
        rows = db.query(CorpusItem).filter(CorpusItem.id.in_(ranked_ids)).all()
        items_by_id = {r.id: r for r in rows}

    out = []
    for cid in ranked_ids:
        row = items_by_id.get(cid)
        raw_text = row.raw_text if row else docs_by_id.get(cid, "")
        structured = row.structured if row else None
        tags = (row.tags if row else None) or []
        direction_out = (row.direction if row else metas_by_id.get(cid, {}).get("direction"))
        score = vec_score.get(cid, rank_score.get(cid, 0.0))
        out.append({
            "id": cid,
            "item_type": row.item_type if row else metas_by_id.get(cid, {}).get("item_type"),
            "raw_text": raw_text,
            "structured": structured,
            "tags": tags,
            "direction": direction_out,
            "score": round(float(score), 4),
        })
    return out


# ============ CRUD ============

def list_corpus(db: Session, item_type: Optional[str] = None, limit: int = 50) -> List[CorpusItem]:
    q = db.query(CorpusItem)
    if item_type:
        q = q.filter(CorpusItem.item_type == item_type)
    return q.order_by(CorpusItem.created_at.desc()).limit(limit).all()


def delete_corpus(item_id: str, db: Session) -> bool:
    item = db.query(CorpusItem).filter(CorpusItem.id == item_id).first()
    if not item:
        return False
    db.delete(item)
    db.commit()
    try:
        collection = get_or_create_collection(get_vector_store(), _CORPUS_COLLECTION)
        collection.delete(ids=[item_id])
    except Exception:  # noqa: BLE001
        pass
    return True


def count_corpus(db: Session) -> Dict[str, int]:
    from sqlalchemy import func
    rows = db.query(CorpusItem.item_type, func.count(CorpusItem.id)).group_by(CorpusItem.item_type).all()
    return {item_type: int(n) for item_type, n in rows}


# ============ 贡献开关（per-user 同意） ============

def set_corpus_consent(db: Session, user_id: str, allow: bool) -> bool:
    from app.models.user import User
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return False
    user.allow_corpus = bool(allow)
    db.commit()
    return True


def get_corpus_consent(db: Session, user_id: str) -> bool:
    from app.models.user import User
    user = db.query(User).filter(User.id == user_id).first()
    return bool(user and user.allow_corpus)
