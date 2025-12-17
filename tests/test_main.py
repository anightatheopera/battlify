import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
import os

# --- SETUP MOCK ENV ---
# Ensure these match your actual .env or docker-compose keys
os.environ["SITE_ADMIN_PASSWORD"] = "testpass"
os.environ["DB_NAME"] = "test_db"
os.environ["SPOTIFY_CLIENT_ID"] = "mock"
os.environ["SPOTIFY_CLIENT_SECRET"] = "mock"

@pytest.mark.asyncio
async def test_homepage_render():
    """
    Check Homepage Structure:
    1. Header & Logo
    2. Admin Login Button
    3. New Tabs Structure (Active vs Past)
    """
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/")
        html = response.text
        
        assert response.status_code == 200
        
        # Header Checks
        assert 'class="header"' in html
        assert 'LORIAN AWARDS' in html
        
        # Auth Checks
        assert 'onclick="loginAdmin()"' in html
        
        # Tab Checks (New Feature)
        assert 'class="tabs"' in html
        assert 'onclick="switchTab(\'active\')"' in html
        assert 'onclick="switchTab(\'past\')"' in html
        
        # List Container Checks
        assert 'id="active-container"' in html
        assert 'id="past-container"' in html

@pytest.mark.asyncio
async def test_admin_lifecycle_with_jwt():
    """
    Full Lifecycle Test with Authentication:
    1. Login (Get Token)
    2. Create Draft (Using Token)
    3. Delete Active Tournament (Using Token)
    """
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        
        # --- STEP 1: LOGIN ---
        login_payload = {"password": "testpass"}
        login_res = await ac.post("/api/admin/login", json=login_payload)
        
        assert login_res.status_code == 200
        data = login_res.json()
        assert "access_token" in data
        token = data["access_token"]
        
        # Prepare Auth Headers
        auth_headers = {"Authorization": f"Bearer {token}"}

        # --- STEP 2: CREATE DRAFT ---
        create_payload = {
            "name": "JWT Lifecycle Test",
            "voting_duration_minutes": 10,
            "urls": [] 
        }
        res = await ac.post("/api/admin/create", json=create_payload, headers=auth_headers)
        assert res.status_code == 200
        t_id = res.json()["tournament_id"]

        # --- STEP 3: FORCE ACTIVE STATUS ---
        # Manually update DB to simulate a started tournament
        from app.database import get_database
        from bson.objectid import ObjectId
        db = get_database()
        db.tournaments.update_one({"_id": ObjectId(t_id)}, {"$set": {"status": "active"}})

        # --- STEP 4: DELETE (Using Token) ---
        del_res = await ac.delete(f"/api/admin/{t_id}", headers=auth_headers)
        
        assert del_res.status_code == 200 
        assert del_res.json()["message"] == "Deleted"

@pytest.mark.asyncio
async def test_vote_page_split_structure():
    """Check if the Vote page serves the correct Static HTML structure for Split Brackets"""
    # Create a dummy tournament directly in DB
    from app.database import get_database
    db = get_database()
    t = db.tournaments.insert_one({
        "name": "Visual Split Test", 
        "status": "active", 
        "rounds": [], 
        "voting_duration_minutes": 60,
        "current_round_index": 0
    })
    t_id = str(t.inserted_id)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get(f"/bracket/{t_id}")
        assert response.status_code == 200
        html = response.text
        
        # Check for the specific CSS classes used in the new Tree View
        assert 'class="bracket-wrapper"' in html
        assert 'id="bracket-left"' in html
        assert 'id="bracket-right"' in html
        assert 'id="bracket-final"' in html
        
        # Verify the header includes the JS logic
        assert '<script src="/static/script.js"></script>' in html