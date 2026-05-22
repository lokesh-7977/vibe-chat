from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.db.schemas.user import UserCreate, UserLogin
from app.services.auth_service import AuthService


class FakeUser:
    def __init__(
        self,
        *,
        user_id=None,
        full_name="Lokesh",
        username="lokesh-1234",
        email="lokesh@example.com",
        password="hashed-password",
        is_active=True,
        is_verified=False,
        is_deleted=False,
    ) -> None:
        self.id = user_id or uuid4()
        self.full_name = full_name
        self.username = username
        self.email = email
        self.password = password
        self.is_active = is_active
        self.is_verified = is_verified
        self.is_deleted = is_deleted


class FakeUserRepository:
    def __init__(self, existing_user=None, active_user=None) -> None:
        self.existing_user = existing_user
        self.active_user = active_user
        self.created_payload = None
        self.save_called = False
        self.db = object()

    def get_by_email(self, email: str):
        return self.existing_user

    def get_active_by_email(self, email: str):
        return self.active_user

    def get_active_by_id(self, user_id):
        if self.active_user and self.active_user.id == user_id:
            return self.active_user
        return None

    def create(self, **user_data):
        self.created_payload = user_data
        self.active_user = FakeUser(
            full_name=user_data["full_name"],
            username=user_data["username"],
            email=user_data["email"],
            password=user_data["password"],
            is_active=user_data["is_active"],
            is_verified=user_data["is_verified"],
            is_deleted=user_data["is_deleted"],
        )
        return self.active_user

    def save(self) -> None:
        self.save_called = True


@pytest.fixture
def request():
    return SimpleNamespace(session={})


def test_register_user_stores_session_and_returns_tokens(monkeypatch, request):
    repository = FakeUserRepository()
    service = AuthService(repository)
    payload = UserCreate(
        full_name="Lokesh",
        email="lokesh@example.com",
        password="secret123",
    )

    monkeypatch.setattr(
        "app.services.auth_service.generate_username",
        lambda *_: "lokesh-4321",
    )
    monkeypatch.setattr(
        "app.services.auth_service.hash_password",
        lambda password: f"hashed::{password}",
    )
    monkeypatch.setattr(
        "app.services.auth_service.create_access_token",
        lambda data: "access-token",
    )
    monkeypatch.setattr(
        "app.services.auth_service.create_refresh_token",
        lambda user_id: f"refresh::{user_id}",
    )

    response = service.register_user(payload, request)

    assert response.success is True
    assert response.data.access_token == "access-token"
    assert response.data.user.username == "lokesh-4321"
    assert repository.created_payload["password"] == "hashed::secret123"
    assert request.session["user_id"] == str(repository.active_user.id)
    assert request.session["refresh_token"] == f"refresh::{repository.active_user.id}"


def test_login_user_rejects_invalid_password(monkeypatch, request):
    repository = FakeUserRepository(active_user=FakeUser(password="stored-hash"))
    service = AuthService(repository)
    payload = UserLogin(email="lokesh@example.com", password="wrongpass")

    monkeypatch.setattr(
        "app.services.auth_service.verify_password",
        lambda plain, hashed: False,
    )

    with pytest.raises(HTTPException) as exc_info:
        service.login_user(payload, request)

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Invalid email or password"


def test_refresh_token_rotates_refresh_token(monkeypatch, request):
    active_user = FakeUser()
    repository = FakeUserRepository(active_user=active_user)
    service = AuthService(repository)
    request.session["user_id"] = str(active_user.id)
    request.session["refresh_token"] = "old-refresh-token"

    monkeypatch.setattr(
        "app.services.auth_service.verify_refresh_token",
        lambda token: str(active_user.id),
    )
    monkeypatch.setattr(
        "app.services.auth_service.create_access_token",
        lambda data: "new-access-token",
    )
    monkeypatch.setattr(
        "app.services.auth_service.create_refresh_token",
        lambda user_id: "new-refresh-token",
    )

    response = service.refresh_token(request)

    assert response.success is True
    assert response.data.access_token == "new-access-token"
    assert request.session["refresh_token"] == "new-refresh-token"


def test_logout_user_requires_authenticated_session(request):
    repository = FakeUserRepository()
    service = AuthService(repository)

    with pytest.raises(HTTPException) as exc_info:
        service.logout_user(request)

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "User not authenticated"


def test_delete_account_marks_user_deleted_and_clears_session(request):
    active_user = FakeUser()
    repository = FakeUserRepository(active_user=active_user)
    service = AuthService(repository)
    request.session["user_id"] = str(active_user.id)
    request.session["refresh_token"] = "refresh-token"

    response = service.delete_account(request)

    assert response.success is True
    assert active_user.is_deleted is True
    assert active_user.is_active is False
    assert repository.save_called is True
    assert request.session == {}
