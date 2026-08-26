"""通用文本工具：技能识别等，供多个业务模块复用。"""

import re
from typing import Dict, List, Set


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


def normalize_text(text: str) -> str:
    text = (text or "").lower()
    text = re.sub(r"[_\-\s]+", " ", text)
    return text


def extract_skills(text: str) -> Set[str]:
    """从文本中识别已知技能。"""
    normalized = normalize_text(text)
    found: Set[str] = set()
    for skill, aliases in SKILL_ALIASES.items():
        if any(alias in normalized for alias in aliases):
            found.add(skill)
    return found
