import pytest
from io import BytesIO
from docx import Document

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


def test_resume_versions_api(client):
    """测试简历版本历史接口"""
    first = client.post(
        "/api/v1/resume/upload",
        json={"raw_text": "张三，3年Python开发经验，熟悉Django", "source_file": "a.txt"},
    )
    assert first.json()["success"] is True
    resume_id = first.json()["data"]["id"]

    client.post(
        "/api/v1/resume/upload",
        json={"raw_text": "张三，5年Python开发经验，熟悉Django和FastAPI", "source_file": "b.txt"},
    )

    versions = client.get(f"/api/v1/resume/{resume_id}/versions")
    assert versions.status_code == 200
    data = versions.json()["data"]
    assert len(data) == 2
    assert data[0]["version"] == 2
    assert data[0]["parsed_json"]["skills"]


def test_resume_upload_docx(client):
    """测试 .docx 简历上传"""
    doc = Document()
    doc.add_paragraph("张三，5年Python开发经验，熟悉Django和FastAPI")
    buffer = BytesIO()
    doc.save(buffer)

    response = client.post(
        "/api/v1/resume/upload-file",
        files={
            "file": (
                "resume.docx",
                buffer.getvalue(),
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        },
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["filename"] == "resume.docx"

    versions = client.get(f"/api/v1/resume/{data['id']}/versions")
    assert versions.status_code == 200
    assert "Django" in versions.json()["data"][0]["raw_text"]
