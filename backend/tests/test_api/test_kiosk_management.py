# test_kiosk_management.py

import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

@pytest.fixture
def superadmin_token():
    # This should be replaced with a real token fixture or mock
    return "Bearer test-superadmin-token"

def test_create_kiosk_user_success(monkeypatch, superadmin_token):
    def mock_create_kiosk_user(db, user_data, current_user):
        return {
            "user_id": 100,
            "username": user_data.username,
            "email": user_data.email,
            "phone": user_data.phone,
            "is_active": user_data.is_active,
            "is_verified": user_data.is_verified,
            "role_name": "kiosk",
            "created_at": "2025-09-19T00:00:00Z",
            "updated_at": None,
            "last_login_at": None
        }

    from backend.app.logic import UserManagementLogic
    monkeypatch.setattr(UserManagementLogic.user_management_logic, "create_kiosk_user", mock_create_kiosk_user)

    response = client.post(
        "/api/kiosk/create",
        json={
            "username": "kiosk_test",
            "password": "StrongPass123",
            "is_active": True,
            "is_verified": False
        },
        headers={"Authorization": superadmin_token}
    )

    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "kiosk_test"
    assert data["role_name"] == "kiosk"