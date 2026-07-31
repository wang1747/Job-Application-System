from app.models.interview import InterviewArticle, InterviewQuestion


def test_article_creation(db_session):
    """测试面经文章创建"""
    article = InterviewArticle(
        user_id="test_user",
        company="ByteDance",
        position="Backend",
        raw_content="Interview experience content",
        source="manual",
    )
    db_session.add(article)
    db_session.commit()
    assert article.id is not None
    assert article.company == "ByteDance"


def test_question_creation(db_session):
    """测试面试题创建"""
    question = InterviewQuestion(
        user_id="test_user",
        question="What is Python?",
        answer="A programming language",
        category="技术",
    )
    db_session.add(question)
    db_session.commit()
    assert question.id is not None
    assert question.category == "技术"


def test_article_question_relation(db_session):
    """测试面经与题目的关联"""
    article = InterviewArticle(
        user_id="test_user",
        company="TestCorp",
        position="Backend",
        raw_content="Some content",
        source="manual",
    )
    db_session.add(article)
    db_session.flush()

    question = InterviewQuestion(
        user_id="test_user",
        article_id=article.id,
        question="Test question?",
    )
    db_session.add(question)
    db_session.commit()

    assert question.article_id == article.id
    assert article.question_list[0].id == question.id
    assert question.article.company == "TestCorp"
    assert question.article.raw_content == "Some content"
    assert question.article.position == "Backend"
    assert question.article.source == "manual"
    assert article.created_at is not None
    assert article.embedding_id is None
    assert article.tags is None
    assert article.difficulty is None


def test_article_import_dedup(client):
    """测试面经导入去重"""
    content = "字节跳动后端一面：自我介绍，讲项目，Redis 缓存穿透。"
    first = client.post(
        "/api/v1/interview/articles",
        json={"company": "ByteDance", "raw_content": content},
    )
    assert first.json()["success"] is True
    first_id = first.json()["data"]["id"]

    second = client.post(
        "/api/v1/interview/articles",
        json={"company": "ByteDance", "raw_content": content + "  "},
    )
    assert second.json()["data"]["duplicate"] is True
    assert second.json()["data"]["id"] == first_id


def test_article_file_upload(client):
    """测试面经文件上传"""
    response = client.post(
        "/api/v1/interview/articles/upload",
        data={"company": "TestCorp"},
        files={"file": ("article.md", "# 面经\n问题：什么是高并发？".encode("utf-8"), "text/markdown")},
    )
    assert response.status_code == 200
    assert response.json()["success"] is True
    assert response.json()["data"]["filename"] == "article.md"
