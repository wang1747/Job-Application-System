import pytest
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
    assert question.user_id == "test_user"
    assert article.user_id == "test_user"
    assert article.user is None
    assert question.user is None
    assert question.article is not None
    assert question.article.raw_content == "Some content"
    assert article.question_list is not None
    assert len(article.question_list) == 1
    assert article.question_list[0] is not None
    assert article.question_list[0].id is not None
    assert article.question_list[0].question == "Test question?"
    assert article.question_list[0].answer is None
    assert article.question_list[0].category is None
    assert article.question_list[0].difficulty is None
    assert article.question_list[0].created_at is not None
    assert article.created_at is not None
    assert article.embedding_id is None
    assert article.tags is None
    assert article.difficulty is None
    assert article.position == "Backend"
    assert question.article.position == "Backend"
    assert question.article.user_id == "test_user"
    assert article.user_id == "test_user"
    assert question.user_id == "test_user"
    assert article.question_list is not None
    assert len(article.question_list) == 1
    assert article.question_list[0].question == "Test question?"
    assert article.question_list[0].id is not None
    assert article.question_list[0].answer is None
    assert article.question_list[0].category is None
    assert article.question_list[0].difficulty is None
    assert article.question_list[0].created_at is not None
    assert article.created_at is not None
    assert article.embedding_id is None
    assert article.tags is None
    assert article.difficulty is None
    assert article.position == "Backend"
    assert question.article.id == article.id
    assert question.article.company == "TestCorp"
    assert question.article.raw_content == "Some content"
    assert question.article.source == "manual"
    assert question.article.question_list is not None
    assert len(question.article.question_list) == 1
    assert question.article.question_list[0].question == "Test question?"
    assert question.article.question_list[0].id is not None
    assert question.article.question_list[0].answer is None
    assert question.article.question_list[0].category is None
    assert question.article.question_list[0].difficulty is None
    assert question.article.question_list[0].created_at is not None
    assert question.article.created_at is not None
    assert question.article.embedding_id is None
    assert question.article.tags is None
    assert question.article.difficulty is None
    assert question.article.position == "Backend"
    assert question.article.id == article.id
    assert question.article.company == "TestCorp"
    assert question.article.raw_content == "Some content"
    assert question.article.source == "manual"
    assert question.article.question_list[0].question == "Test question?"
    assert question.article.question_list[0].id is not None
    assert question.article.question_list[0].answer is None
    assert question.article.question_list[0].category is None
    assert question.article.question_list[0].difficulty is None
    assert question.article.question_list[0].created_at is not None
    assert question.article.created_at is not None
    assert question.article.embedding_id is None
    assert question.article.tags is None
    assert question.article.difficulty is None
    assert question.article.position == "Backend"
