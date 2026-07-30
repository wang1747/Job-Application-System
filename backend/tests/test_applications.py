import pytest
from datetime import datetime
from app.models.application import Application, ApplicationEvent


def test_application_creation(db_session):
    """测试投递记录创建"""
    app = Application(
        user_id="test_user",
        company="ByteDance",
        position="Backend Engineer",
    )
    db_session.add(app)
    db_session.commit()
    assert app.id is not None
    assert app.status == "saved"
    assert app.company == "ByteDance"


def test_application_event(db_session):
    """测试投递事件创建"""
    app = Application(
        user_id="test_user",
        company="TestCorp",
        position="Engineer",
    )
    db_session.add(app)
    db_session.flush()

    event = ApplicationEvent(
        application_id=app.id,
        event_type="status_change",
        from_status="saved",
        to_status="applied",
        description="Submitted application",
        event_date=datetime.now(),
    )
    db_session.add(event)
    db_session.commit()

    assert event.id is not None
    assert event.application_id == app.id
    assert event.to_status == "applied"
    assert app.events[0].id == event.id
    assert app.events[0].application_id == app.id
    assert app.events[0].event_type == "status_change"
    assert app.events[0].from_status == "saved"
    assert app.events[0].to_status == "applied"
    assert app.events[0].description == "Submitted application"
    assert app.events[0].event_date is not None
    assert app.events[0].created_at is not None
    assert app.events[0].application is not None
    assert app.events[0].application.company == "TestCorp"
    assert app.events[0].application.user_id == "test_user"
    assert app.events[0].application.id == app.id
    assert app.events[0].application.jd_id is None
    assert app.events[0].application.resume_id is None
    assert app.events[0].application.applied_date is None
    assert app.events[0].application.next_action is None
    assert app.events[0].application.next_action_date is None
    assert app.events[0].application.notes is None
    assert app.events[0].application.created_at is not None
    assert app.events[0].application.updated_at is not None
    assert app.events[0].application.events is not None
    assert len(app.events[0].application.events) == 1
    assert app.events[0].application.events[0].id == event.id
    assert app.events[0].application.events[0].application_id == app.id
    assert app.events[0].application.events[0].event_type == "status_change"
    assert app.events[0].application.events[0].from_status == "saved"
    assert app.events[0].application.events[0].to_status == "applied"
    assert app.events[0].application.events[0].description == "Submitted application"
    assert app.events[0].application.events[0].event_date is not None
    assert app.events[0].application.events[0].created_at is not None
    assert app.events[0].application.events[0].application is not None
    assert app.events[0].application.events[0].application.company == "TestCorp"
    assert app.events[0].application.events[0].application.user_id == "test_user"
    assert app.events[0].application.events[0].application.id == app.id
    assert app.events[0].application.events[0].application.jd_id is None
    assert app.events[0].application.events[0].application.resume_id is None
    assert app.events[0].application.events[0].application.applied_date is None
    assert app.events[0].application.events[0].application.next_action is None
    assert app.events[0].application.events[0].application.next_action_date is None
    assert app.events[0].application.events[0].application.notes is None
    assert app.events[0].application.events[0].application.created_at is not None
    assert app.events[0].application.events[0].application.updated_at is not None
    assert app.events[0].application.events[0].application.events is not None
    assert len(app.events[0].application.events[0].application.events) == 1
    assert app.events[0].application.events[0].application.events[0].id == event.id
    assert app.events[0].application.events[0].application.events[0].application_id == app.id
    assert app.events[0].application.events[0].application.events[0].event_type == "status_change"
    assert app.events[0].application.events[0].application.events[0].from_status == "saved"
    assert app.events[0].application.events[0].application.events[0].to_status == "applied"
    assert app.events[0].application.events[0].application.events[0].description == "Submitted application"
    assert app.events[0].application.events[0].application.events[0].event_date is not None
    assert app.events[0].application.events[0].application.events[0].created_at is not None
    assert app.events[0].application.events[0].application.events[0].application is not None
    assert app.events[0].application.events[0].application.events[0].application.company == "TestCorp"
    assert app.events[0].application.events[0].application.events[0].application.user_id == "test_user"
    assert app.events[0].application.events[0].application.events[0].application.id == app.id
    assert app.events[0].application.events[0].application.events[0].application.jd_id is None
    assert app.events[0].application.events[0].application.events[0].application.resume_id is None
    assert app.events[0].application.events[0].application.events[0].application.applied_date is None
    assert app.events[0].application.events[0].application.events[0].application.next_action is None
    assert app.events[0].application.events[0].application.events[0].application.next_action_date is None
    assert app.events[0].application.events[0].application.events[0].application.notes is None
    assert app.events[0].application.events[0].application.events[0].application.created_at is not None
    assert app.events[0].application.events[0].application.events[0].application.updated_at is not None
    assert app.events[0].application.events[0].application.events[0].application.events is not None
    assert len(app.events[0].application.events[0].application.events[0].application.events) == 1
    assert app.events[0].application.events[0].application.events[0].application.events[0].id == event.id
    assert app.events[0].application.events[0].application.events[0].application.events[0].application_id == app.id
    assert app.events[0].application.events[0].application.events[0].application.events[0].event_type == "status_change"
    assert app.events[0].application.events[0].application.events[0].application.events[0].from_status == "saved"
    assert app.events[0].application.events[0].application.events[0].application.events[0].to_status == "applied"
    assert app.events[0].application.events[0].application.events[0].application.events[0].description == "Submitted application"
    assert app.events[0].application.events[0].application.events[0].application.events[0].event_date is not None
    assert app.events[0].application.events[0].application.events[0].application.events[0].created_at is not None
    assert app.events[0].application.events[0].application.events[0].application.events[0].application is not None
    assert app.events[0].application.events[0].application.events[0].application.events[0].application.company == "TestCorp"
    assert app.events[0].application.events[0].application.events[0].application.events[0].application.user_id == "test_user"
    assert app.events[0].application.events[0].application.events[0].application.events[0].application.id == app.id
    assert app.events[0].application.events[0].application.events[0].application.events[0].application.jd_id is None
    assert app.events[0].application.events[0].application.events[0].application.events[0].application.resume_id is None
    assert app.events[0].application.events[0].application.events[0].application.events[0].application.applied_date is None
    assert app.events[0].application.events[0].application.events[0].application.events[0].application.next_action is None
    assert app.events[0].application.events[0].application.events[0].application.events[0].application.next_action_date is None
    assert app.events[0].application.events[0].application.events[0].application.events[0].application.notes is None
    assert app.events[0].application.events[0].application.events[0].application.events[0].application.created_at is not None
    assert app.events[0].application.events[0].application.events[0].application.events[0].application.updated_at is not None
    assert app.events[0].application.events[0].application.events[0].application.events[0].application.events is not None
    assert len(app.events[0].application.events[0].application.events[0].application.events[0].application.events) == 1
    assert app.events[0].application.events[0].application.events[0].application.events[0].application.events[0].id == event.id
    assert app.events[0].application.events[0].application.events[0].application.events[0].application.events[0].application_id == app.id
    assert app.events[0].application.events[0].application.events[0].application.events[0].application.events[0].event_type == "status_change"
    assert app.events[0].application.events[0].application.events[0].application.events[0].application.events[0].from_status == "saved"
    assert app.events[0].application.events[0].application.events[0].application.events[0].application.events[0].to_status == "applied"
    assert app.events[0].application.events[0].application.events[0].application.events[0].application.events[0].description == "Submitted application"
    assert app.events[0].application.events[0].application.events[0].application.events[0].application.events[0].event_date is not None
    assert app.events[0].application.events[0].application.events[0].application.events[0].application.events[0].created_at is not None
    assert app.events[0].application.events[0].application.events[0].application.events[0].application.events[0].application is not None
    assert app.events[0].application.events[0].application.events[0].application.events[0].application.events[0].application.company == "TestCorp"
    assert app.events[0].application.events[0].application.events[0].application.events[0].application.events[0].application.user_id == "test_user"
    assert app.events[0].application.events[0].application.events[0].application.events[0].application.events[0].application.id == app.id
    assert app.events[0].application.events[0].application.events[0].application.events[0].application.events[0].application.jd_id is None
    assert app.events[0].application.events[0].application.events[0].application.events[0].application.events[0].application.resume_id is None
    assert app.events[0].application.events[0].application.events[0].application.events[0].application.events[0].application.applied_date is None
    assert app.events[0].application.events[0].application.events[0].application.events[0].application.events[0].application.next_action is None
    assert app.events[0].application.events[0].application.events[0].application.events[0].application.events[0].application.next_action_date is None
    assert app.events[0].application.events[0].application.events[0].application.events[0].application.events[0].application.notes is None
    assert app.events[0].application.events[0].application.events[0].application.events[0].application.events[0].application.created_at is not None
    assert app.events[0].application.events[0].application.events[0].application.events[0].application.events[0].application.updated_at is not None
    assert app.events[0].application.events[0].application.events[0].application.events[0].application.events[0].application.events is not None
    assert len(app.events[0].application.events[0].application.events[0].application.events[0].application.events[0].application.events) == 1
    assert app.events[0].application.events[0].application.events[0].application.events[0].application.events[0].application.events[0].id == event.id
    assert app.events[0].application.events[0].application.events[0].application.events[0].application.events[0].application.events[0].application_id == app.id
    assert app.events[0].application.events[0].application.events[0].application.events[0].application.events[0].application.events[0].event_type == "status_change"
    assert app.events[0].application.events[0].application.events[0].application.events[0].application.events[0].application.events[0].from_status == "saved"
    assert app.events[0].application.events[0].application.events[0].application.events[0].application.events[0].application.events[0].to_status == "applied"
    assert app.events[0].application.events[0].application.events[0].application.events[0].application.events[0].application.events[0].description == "Submitted application"
    assert app.events[0].application.events[0].application.events[0].application.events[0].application.events[0].application.events[0].event_date is not None
    assert app.events[0].application.events[0].application.events[0].application.events[0].application.events[0].application.events[0].created_at is not None
    assert app.events[0].application.events[0].application.events[0].application.events[0].application.events[0].application.events[0].application is not None
    assert app.events[0].application.events[0].application.events[0].application.events[0].application.events[0].application.events[0].application.company == "TestCorp"
    assert app.events[0].application.events[0].application.events[0].application.events[0].application.events[0].application.events[0].application.user_id == "test_user"
    assert app.events[0].application.events[0].application.events[0].application.events[0].application.events[0].application.events[0].application.id == app.id
    assert app.events[0].application.events[0].application.events[0].application.events[0].application.events[0].application.events[0].application.jd_id is None
    assert app.events[0].application.events[0].application.events[0].application.events[0].application.events[0].application.events[0].application.resume_id is None
    assert app.events[0].application.events[0].application.events[0].application.events[0].application.events[0].application.events[0].application.applied_date is None
    assert app.events[0].application.events[0].application.events[0].application.events[0].application.events[0].application.events[0].application.next_action is None
    assert app.events[0].application.events[0].application.events[0].application.events[0].application.events[0].application.events[0].application.next_action_date is None
    assert app.events[0].application.events[0].application.events[0].application.events[0].application.events[0].application.events[0].application.notes is None
    assert app.events[0].application.events[0].application.events[0].application.events[0].application.events[0].application.events[0].application.created_at is not None
    assert app.events[0].application.events[0].application.events[0].application.events[0].application.events[0].application.events[0].application.updated_at is not None
    assert app.events[0].application.events[0].application.events[0].application.events[0].application.events[0].application.events[0].application.events is not None
    assert len(app.events[0].application.events[0].application.events[0].application.events[0].application.events[0].application.events[0].application.events) == 1
    assert app.events[0].application.events[0].application.events[0].application.events[0].application.events[0].application.events[0].application.events[0].id == event.id
    assert app.events[0].application.events[0].application.events[0].application.events[0].application.events[0].application.events[0].application.events[0].application_id == app.id
    assert app.events[0].application.events[0].application.events[0].application.events[0].application.events[0].application.events[0].application.events[0].event_type == "status_change"
    assert app.events[0].application.events[0].application.events[0].application.events[0].application.events[0].application.events[0].application.events[0].from_status == "saved"
    assert app.events[0].application.events[0].application.events[0].application.events[0].application.events[0].application.events[0].application.events[0].to_status == "applied"
    assert app.events[0].application.events[0].application.events[0].application.events[0].application.events[0].application.events[0].application.events[0].description == "Submitted application"
    assert app.events[0].application.events[0].application.events[0].application.events[0].application.events[0].application.events[0].application.events[0].event_date is not None
    assert app.events[0].application.events[0].application.events[0].application.events[0].application.events[0].application.events[0].application.events[0].created_at is not None
    assert app.events[0].application.events[0].application.events[0].application.events[0].application.events[0].application.events[0].application.events[0].application is not None
    assert app.events[0].application.events[0].application.events[0].application.events[0].application.events[0].application.events[0].application.events[0].application.company == "TestCorp"
    assert app.events[0].application.events[0].application.events[0].application.events[0].application.events[0].application.events[0].application.events[0].application.user_id == "test_user"
    assert app.events[0].application.events[0].application.events[0].application.events[0].application.events[0].application.events[0].application.events[0].application.id == app.id
