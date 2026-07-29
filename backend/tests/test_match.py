import pytest
from app.models.match import MatchResult


def test_match_result_creation(db_session):
    """测试匹配结果模型创建"""
    match = MatchResult(
        jd_id="jd-1",
        resume_id="resume-1",
        score=85.5,
    )
    db_session.add(match)
    db_session.commit()
    assert match.id is not None
    assert match.score == 85.5
    assert match.jd_id == "jd-1"
    assert match.resume_id == "resume-1"


def test_match_default_score(db_session):
    """测试匹配分默认值"""
    match = MatchResult(jd_id="jd-2", resume_id="resume-2", score=0.0)
    db_session.add(match)
    db_session.commit()
    assert match.score == 0.0
    assert match.skill_match_detail is None
    assert match.gap_analysis is None
    assert match.suggestion is None
    assert match.created_at is not None
    assert match.jd is None
    assert match.resume is None
