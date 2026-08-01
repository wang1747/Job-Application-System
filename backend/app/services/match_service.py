import hashlib
import math
import re
from typing import Dict, List, Optional, Set

from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.jd import JobDescription
from app.models.match import MatchResult
from app.models.resume import Resume
from app.core.vector_store import get_vector_store, get_or_create_collection

_EMBEDDING_DIM = 384
_SEMANTIC_COLLECTION = "jd_resume_matches"

# ============ 本地技能词典匹配（保留作为降级方案） ============

SKILL_ALIASES: Dict[str, List[str]] = {
    "Python": ["python", "python3", "py"],
    "Java": ["java"],
    "Go": ["go", "golang"],
    "C++": ["c++", "cpp"],
    "JavaScript": ["javascript", "js"],
    "TypeScript": ["typescript", "ts"],
    "React": ["react"],
    "Vue": ["vue", "vuejs"],
    "Node.js": ["node", "nodejs", "node.js"],
    "FastAPI": ["fastapi"],
    "Flask": ["flask"],
    "Django": ["django"],
    "SQL": ["sql", "sqlite"],
    "MySQL": ["mysql"],
    "PostgreSQL": ["postgresql", "postgres"],
    "Redis": ["redis"],
    "Docker": ["docker"],
    "Kubernetes": ["kubernetes", "k8s"],
    "AWS": ["aws", "亚马逊云"],
    "Git": ["git", "github", "gitlab"],
    "Linux": ["linux", "unix"],
    "Spring Boot": ["spring boot", "spring"],
    "Kafka": ["kafka"],
    "Nginx": ["nginx"],
    "CI/CD": ["ci/cd", "cicd", "jenkins"],
    "微服务": ["微服务", "microservice", "micro services"],
    "高并发": ["高并发", "high concurrency", "high-concurrency"],
    "分布式": ["分布式", "distributed"],
    "消息队列": ["消息队列", "message queue", "mq"],
    "RESTful API": ["restful", "rest api", "rest"],
    "算法": ["算法", "algorithm", "leetcode"],
    "机器学习": ["机器学习", "machine learning", "ml"],
    "深度学习": ["深度学习", "deep learning", "dl"],
    "数据分析": ["数据分析", "data analysis"],
    "测试": ["测试", "pytest", "单元测试", "unit test"],
    "安全": ["安全", "security"],
}


def _normalize(text: str) -> str:
    text = (text or "").lower()
    text = re.sub(r"[_\-\s]+", " ", text)
    return text


def _extract_skills(text: str) -> Set[str]:
    """从文本中识别已知技能"""
    normalized = _normalize(text)
    found: Set[str] = set()
    for skill, aliases in SKILL_ALIASES.items():
        if any(alias in normalized for alias in aliases):
            found.add(skill)
    return found


def _skill_sources(jd: JobDescription, resume: Resume) -> tuple:
    jd_parts = [
        jd.raw_text or "",
        " ".join(jd.must_have or []),
        " ".join(jd.nice_to_have or []),
        " ".join(
            value
            for values in (jd.tech_stack or {}).values()
            if isinstance(values, list)
            for value in values
        ),
    ]
    resume_parsed = resume.parsed_json or {}
    resume_parts = [
        resume.raw_text or "",
        " ".join(resume_parsed.get("skills", []) if isinstance(resume_parsed.get("skills"), list) else []),
    ]
    return " ".join(jd_parts), " ".join(resume_parts)


def _extract_skill_aliases(term: str) -> List[str]:
    """返回某个技能词可能命中的别名"""
    normalized = _normalize(term)
    return [normalized] + [alias for aliases in SKILL_ALIASES.values() for alias in aliases if alias in normalized]


def _persist_match(
    jd_id: str,
    resume_id: str,
    score: int,
    matched: List[str],
    missing: List[str],
    partial: List[str],
    suggestion: str,
    db: Session,
) -> MatchResult:
    existing = db.query(MatchResult).filter(
        MatchResult.jd_id == jd_id,
        MatchResult.resume_id == resume_id,
    ).first()
    if existing:
        existing.score = score
        existing.skill_match_detail = {"matched": matched, "missing": missing, "partial": partial}
        existing.gap_analysis = {"hard_gap": missing, "soft_gap": partial, "suggestion": suggestion}
        existing.suggestion = suggestion
        db.commit()
        db.refresh(existing)
        return existing
    match = MatchResult(
        jd_id=jd_id,
        resume_id=resume_id,
        score=score,
        skill_match_detail={"matched": matched, "missing": missing, "partial": partial},
        gap_analysis={"hard_gap": missing, "soft_gap": partial, "suggestion": suggestion},
        suggestion=suggestion,
    )
    db.add(match)
    db.commit()
    db.refresh(match)
    return match


# ============ 语义匹配（ChromaDB 增强） ============

def _tokenize_for_embedding(text: str) -> List[str]:
    """将中英文文本拆成词元和汉字 n-gram，供本地向量化使用"""
    text = (text or "").lower()
    tokens = re.findall(r"[a-z0-9]+", text)
    han = re.findall(r"[\u4e00-\u9fff]", text)
    tokens.extend(han)
    tokens.extend("".join(han[i:i + 2]) for i in range(len(han) - 1))
    return tokens


def _get_embedding(text: str) -> List[float]:
    """本地确定性向量化：不依赖外网，适合 DeepSeek 无 embedding 接口的场景"""
    vector = [0.0] * _EMBEDDING_DIM
    for token in _tokenize_for_embedding(text)[:2000]:
        digest = hashlib.md5(token.encode("utf-8")).digest()
        index = int.from_bytes(digest[:4], "big") % _EMBEDDING_DIM
        vector[index] += 1.0
    norm = math.sqrt(sum(value * value for value in vector))
    if norm == 0:
        return vector
    return [value / norm for value in vector]


def _semantic_score(jd_id: str, jd_text: str, resume_text: str) -> int:
    """将 JD 向量写入 ChromaDB，再用简历向量做余弦相似度查询"""
    try:
        client = get_vector_store()
        collection = get_or_create_collection(
            client,
            _SEMANTIC_COLLECTION,
            metadata={"hnsw:space": "cosine"},
        )
        collection.upsert(
            ids=[jd_id],
            embeddings=[_get_embedding(jd_text)],
            metadatas=[{"jd_id": jd_id}],
        )

        resume_embedding = _get_embedding(resume_text)
        results = collection.query(
            query_embeddings=[resume_embedding],
            n_results=1,
            where={"jd_id": jd_id},
            include=["distances"],
        )

        if results.get("ids") and results["ids"] and results["ids"][0]:
            distance = results["distances"][0][0]
            similarity = max(0.0, min(1.0, 1.0 - distance))
            return int(round(similarity * 100))
        return 0
    except Exception as e:
        print(f"[WARN] 语义匹配失败，使用本地匹配: {e}")
        return 0


# ============ 主匹配函数（混合方案） ============

def calculate_match(jd_id: str, resume_id: str, db: Session) -> dict:
    """
    计算 JD 与简历的匹配度
    优先使用 ChromaDB 语义匹配，降级使用本地技能词典
    """
    settings = get_settings()
    jd = db.query(JobDescription).filter(
        JobDescription.id == jd_id,
        JobDescription.user_id == settings.default_user_id,
    ).first()
    resume = db.query(Resume).filter(
        Resume.id == resume_id,
        Resume.user_id == settings.default_user_id,
    ).first()
    if not jd:
        raise ValueError("JD 不存在")
    if not resume:
        raise ValueError("简历不存在")

    jd_text, resume_text = _skill_sources(jd, resume)
    
    # 1. 本地技能词典匹配
    jd_skills = _extract_skills(jd_text)
    resume_skills = _extract_skills(resume_text)

    matched = sorted(jd_skills & resume_skills)
    missing = sorted(jd_skills - resume_skills)
    partial = []
    for item in (jd.nice_to_have or []):
        if item and not any(alias in _normalize(resume_text) for alias in _extract_skill_aliases(item)):
            partial.append(item)

    hard_weight = 12
    nice_weight = 4
    local_score = max(0, min(100, 100 - len(missing) * hard_weight - len(partial) * nice_weight))
    
    # 2. 语义匹配（ChromaDB）
    semantic_score = _semantic_score(jd.id, jd_text, resume_text)
    
    # 3. 混合分数：语义匹配占 40%，本地匹配占 60%
    if semantic_score > 0:
        final_score = int(semantic_score * 0.4 + local_score * 0.6)
    else:
        final_score = local_score
    
    suggestion = (
        "匹配度较高，可以直接投递。"
        if final_score >= 80
        else "建议补充缺失技能或相关项目经验后再投递。"
    )

    match = _persist_match(
        jd_id=jd_id,
        resume_id=resume_id,
        score=final_score,
        matched=matched,
        missing=missing,
        partial=partial,
        suggestion=suggestion,
        db=db,
    )
    return {
        "id": match.id,
        "jd_id": jd_id,
        "resume_id": resume_id,
        "company": jd.company,
        "position": jd.position,
        "score": match.score,
        "skill_match_detail": match.skill_match_detail,
        "gap_analysis": match.gap_analysis,
        "suggestion": match.suggestion,
        "created_at": match.created_at,
    }


def get_match_detail(match_id: str, db: Session) -> Optional[dict]:
    """获取单条匹配结果详情"""
    settings = get_settings()
    match = db.query(MatchResult).join(
        JobDescription, MatchResult.jd_id == JobDescription.id
    ).filter(
        MatchResult.id == match_id,
        JobDescription.user_id == settings.default_user_id,
    ).first()
    if not match:
        return None
    return {
        "id": match.id,
        "jd_id": match.jd_id,
        "resume_id": match.resume_id,
        "score": match.score,
        "skill_match_detail": match.skill_match_detail,
        "gap_analysis": match.gap_analysis,
        "suggestion": match.suggestion,
        "created_at": match.created_at,
    }


def get_rankings(db: Session) -> List[dict]:
    """获取当前用户按匹配度排序的 JD 列表"""
    settings = get_settings()
    rows = db.query(MatchResult).join(
        JobDescription, MatchResult.jd_id == JobDescription.id
    ).filter(
        JobDescription.user_id == settings.default_user_id
    ).order_by(MatchResult.score.desc()).all()
    return [
        {
            "id": row.id,
            "jd_id": row.jd_id,
            "resume_id": row.resume_id,
            "company": row.jd.company,
            "position": row.jd.position,
            "score": row.score,
            "suggestion": row.suggestion,
            "created_at": row.created_at,
        }
        for row in rows
    ]
