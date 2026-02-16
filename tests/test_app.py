"""
Tests for the Mergington High School API
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app

client = TestClient(app)


class TestRootEndpoint:
    """Tests for the root endpoint"""

    def test_root_redirect(self):
        """Test that root redirects to static/index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestGetActivities:
    """Tests for the GET /activities endpoint"""

    def test_get_activities_success(self):
        """Test that activities endpoint returns all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert "Chess Club" in data
        assert "Basketball" in data
        assert "Tennis Club" in data

    def test_get_activities_structure(self):
        """Test that each activity has required fields"""
        response = client.get("/activities")
        data = response.json()
        for activity_name, activity_data in data.items():
            assert "description" in activity_data
            assert "schedule" in activity_data
            assert "max_participants" in activity_data
            assert "participants" in activity_data
            assert isinstance(activity_data["participants"], list)


class TestSignup:
    """Tests for the POST /activities/{activity_name}/signup endpoint"""

    def test_signup_success(self):
        """Test successful signup for an activity"""
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": "newstudent@mergington.edu"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "newstudent@mergington.edu" in data["message"]

    def test_signup_nonexistent_activity(self):
        """Test signup for an activity that doesn't exist"""
        response = client.post(
            "/activities/Nonexistent Club/signup",
            params={"email": "student@mergington.edu"}
        )
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]

    def test_signup_duplicate_student(self):
        """Test that a student cannot sign up for the same activity twice"""
        email = "duplicate@mergington.edu"
        activity = "Drama Club"

        # First signup should succeed
        response1 = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        assert response1.status_code == 200

        # Second signup should fail
        response2 = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        assert response2.status_code == 400
        data = response2.json()
        assert "already signed up" in data["detail"]

    def test_signup_adds_to_participants(self):
        """Test that signup adds student to activity participants"""
        email = "verify@mergington.edu"
        activity = "Science Club"

        # Get activities before signup
        response_before = client.get("/activities")
        participants_before = response_before.json()[activity]["participants"]

        # Signup
        client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )

        # Get activities after signup
        response_after = client.get("/activities")
        participants_after = response_after.json()[activity]["participants"]

        assert len(participants_after) == len(participants_before) + 1
        assert email in participants_after


class TestUnregister:
    """Tests for the DELETE /activities/{activity_name}/signup endpoint"""

    def test_unregister_success(self):
        """Test successful unregistration from an activity"""
        email = "unregister@mergington.edu"
        activity = "Programming Class"

        # Signup first
        client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )

        # Then unregister
        response = client.delete(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        assert response.status_code == 200
        data = response.json()
        assert "Unregistered" in data["message"]

    def test_unregister_nonexistent_activity(self):
        """Test unregistration from an activity that doesn't exist"""
        response = client.delete(
            "/activities/Nonexistent Club/signup",
            params={"email": "student@mergington.edu"}
        )
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]

    def test_unregister_not_registered_student(self):
        """Test unregistration by a student not signed up"""
        response = client.delete(
            "/activities/Basketball/signup",
            params={"email": "notregistered@mergington.edu"}
        )
        assert response.status_code == 400
        data = response.json()
        assert "not signed up" in data["detail"]

    def test_unregister_removes_from_participants(self):
        """Test that unregister removes student from activity participants"""
        email = "remove@mergington.edu"
        activity = "Gym Class"

        # Signup
        client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )

        # Get participants before unregister
        response_before = client.get("/activities")
        participants_before = response_before.json()[activity]["participants"]
        assert email in participants_before

        # Unregister
        client.delete(
            f"/activities/{activity}/signup",
            params={"email": email}
        )

        # Get participants after unregister
        response_after = client.get("/activities")
        participants_after = response_after.json()[activity]["participants"]
        assert email not in participants_after
        assert len(participants_after) == len(participants_before) - 1
