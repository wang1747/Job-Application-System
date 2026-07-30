import pytest
from app.models.jd import JobDescription


def test_jd_model_creation(db_session):
    """测试 JD 模型创建"""
    jd = JobDescription(
        user_id="test_user",
        raw_text="Test JD text",
        company="TestCorp",
        position="Engineer",
    )
    db_session.add(jd)
    db_session.commit()
    assert jd.id is not None
    assert jd.company == "TestCorp"
    assert jd.position == "Engineer"


def test_jd_parse_api(client, sample_jd_text):
    """测试 JD 解析 API"""
    response = client.post("/api/v1/jd/parse", json={"raw_text": sample_jd_text})
    assert response.status_code == 200
    data = response.json()
    assert "success" in data


def test_jd_list_empty(db_session):
    """测试空 JD 列表"""
    from app.config import get_settings
    settings = get_settings()
    jds = db_session.query(JobDescription).filter(
        JobDescription.user_id == settings.default_user_id
    ).all()
    assert len(jds) == 0
