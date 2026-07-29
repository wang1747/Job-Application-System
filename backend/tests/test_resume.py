import pytest
from app.models.resume import Resume


def test_resume_model_creation(db_session):
    """测试简历模型创建"""
    resume = Resume(
        user_id="test_user",
        version=1,
        raw_text="Test resume content",
        source_file="test.pdf",
    )
    db_session.add(resume)
    db_session.commit()
    assert resume.id is not None
    assert resume.version == 1


def test_resume_list_empty(db_session):
    """测试空简历列表"""
    resumes = db_session.query(Resume).all()
    assert len(resumes) == 0
