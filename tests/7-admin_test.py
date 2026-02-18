import pytest
from httpx import AsyncClient, ASGITransport
from main import app
from .MockUser import MockUser
from app.database.init import init_db
import uuid


@pytest.mark.asyncio(loop_scope="session")
async def test_non_admin_cannot_access_admin_routes(authenticated_user: MockUser):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        r = await ac.get(
            "/admin/clients",
            headers={"x-api-key": authenticated_user.api_key},
        )

    assert r.status_code == 403, f"Expected 403, got {r.status_code}: {r.text}"


@pytest.mark.asyncio(loop_scope="session")
async def test_admin_can_create_update_delete_client(admin_user: MockUser):
    """Happy path for admin management endpoints.

    This test does everything on one client so we don't leave junk behind.
    """
    victim = MockUser()

    # 1) Admin creates a client
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        created = await ac.post(
            "/admin/clients",
            headers={"x-api-key": admin_user.api_key},
            json={
                "email": victim.email,
                "password": victim.password,
                "is_admin": False,
            },
        )

    assert created.status_code in (200, 201), f"Create failed: {created.status_code} {created.text}"
    created_data = created.json().get("data")
    assert created_data and "id" in created_data and "api_key" in created_data, f"Bad create response: {created.text}"
    victim_id = str(created_data["id"])
    victim_uuid = uuid.UUID(victim_id)

    # Confirm in DB
    pool = await init_db()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT id, email, is_admin, is_active, deleted_at
            FROM clients
            WHERE id = $1
            """,
            victim_uuid,
        )
    assert row is not None
    assert row["email"] == victim.email
    assert row["is_admin"] is False
    assert row["deleted_at"] is None

    # 2) Admin updates that client
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        updated = await ac.patch(
            f"/admin/clients/{victim_id}",
            headers={"x-api-key": admin_user.api_key},
            json={
                "subscription": "pro",
                "is_active": True,
            },
        )

    assert updated.status_code in (200, 201), f"Update failed: {updated.status_code} {updated.text}"

    async with pool.acquire() as conn:
        row2 = await conn.fetchrow(
            """
            SELECT subscription, is_active
            FROM clients
            WHERE id = $1
            """,
            victim_uuid,
        )
    assert row2 is not None
    assert row2["subscription"] == "pro"
    assert row2["is_active"] is True

    # 3) Admin deletes that client
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        deleted = await ac.delete(
            f"/admin/clients/{victim_id}",
            headers={"x-api-key": admin_user.api_key},
        )

    assert deleted.status_code == 204, f"Delete failed: {deleted.status_code} {deleted.text}"

    async with pool.acquire() as conn:
        row3 = await conn.fetchrow(
            """
            SELECT deleted_at, is_active
            FROM clients
            WHERE id = $1
            """,
            victim_uuid,
        )
    assert row3 is not None
    assert row3["deleted_at"] is not None
    assert row3["is_active"] is False