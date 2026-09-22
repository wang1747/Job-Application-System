from app.modules.resume.structure import parse_resume_structure
from app.modules.resume_generation.render import render_resume_text


def test_render_resume_text_is_parseable():
    structured = {
        "name": "张三",
        "position": "Python 后端实习",
        "contact": {
            "phone": "13800138000",
            "email": "zhangsan@example.com",
            "github": "https://github.com/zhangsan",
        },
        "summary": "数据科学与大数据技术专业，具备 Python 后端开发能力。",
        "education": [
            {
                "school": "河北环境工程学院",
                "major": "数据科学与大数据技术",
                "degree": "本科",
                "start": "2023-09",
                "end": "2027-06",
                "detail": "",
            }
        ],
        "experiences": [
            {
                "type": "project",
                "name": "OfferFlow 求职系统",
                "role": "后端开发",
                "start": "2026-03",
                "end": "2026-08",
                "bullets": ["使用 FastAPI 搭建后端"],
            }
        ],
        "skills": ["Python", "FastAPI"],
        "certifications": [],
    }
    text = render_resume_text(structured)
    parsed = parse_resume_structure(text)
    assert parsed.name == "张三"
    titles = [section.title for section in parsed.sections]
    assert "教育经历" in titles
    assert "项目经历" in titles


def test_resume_generate_api(client):
    response = client.post(
        "/api/v1/resume-generation/generate",
        json={
            "name": "张三",
            "position": "Python 后端实习",
            "phone": "13800138000",
            "email": "zhangsan@example.com",
            "education": "河北环境工程学院，数据科学与大数据技术，2027届",
            "experience": "OfferFlow 求职 Agent 系统",
            "skills": "Python、FastAPI、Docker",
            "jd_text": "Python 后端实习，要求熟悉 FastAPI",
        },
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["resume_text"]
    assert data["id"]
    assert data["version"] == 1
    assert data["name"] == "张三"
    assert data["experiences"]
    assert "教育经历" in data["sections"]

    exported = client.get(f"/api/v1/resume/{data['id']}/export?format=word")
    assert exported.status_code == 200


def test_resume_regenerate_section_api(client):
    generate = client.post(
        "/api/v1/resume-generation/generate",
        json={
            "name": "张三",
            "position": "Python 后端实习",
            "education": "河北环境工程学院，数据科学与大数据技术，2027届",
            "experience": "OfferFlow 求职 Agent 系统",
            "skills": "Python、FastAPI",
            "jd_text": "Python 后端实习，要求熟悉 FastAPI",
        },
    )
    gen_data = generate.json()["data"]

    response = client.post(
        "/api/v1/resume-generation/regenerate-section",
        json={
            "resume_id": gen_data["id"],
            "structured": {
                "name": gen_data["name"],
                "position": gen_data["position"],
                "contact": gen_data["contact"],
                "summary": gen_data["summary"],
                "education": gen_data["education"],
                "experiences": gen_data["experiences"],
                "skills": gen_data["skills"],
                "certifications": gen_data["certifications"],
            },
            "section": "summary",
            "jd_text": "Python 后端实习，要求熟悉 FastAPI",
        },
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["id"] == gen_data["id"]
    assert data["resume_text"]
    assert "已重新生成" in data["tips"]
    assert "score" in data["ats"]
