"""
Tests for the Mergington High School API activities endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


class TestGetActivities:
    """Test cases for GET /activities endpoint."""

    def test_get_all_activities_returns_200(self, client):
        """Verify endpoint returns 200 status and activities dict."""
        response = client.get("/activities")
        assert response.status_code == 200
        assert isinstance(response.json(), dict)

    def test_get_all_activities_has_expected_structure(self, client):
        """Verify response includes all required fields for each activity."""
        response = client.get("/activities")
        activities = response.json()
        
        # Verify we have activities
        assert len(activities) > 0
        
        # Verify each activity has required fields
        for activity_name, activity_data in activities.items():
            assert isinstance(activity_name, str)
            assert "description" in activity_data
            assert "schedule" in activity_data
            assert "max_participants" in activity_data
            assert "participants" in activity_data
            assert isinstance(activity_data["participants"], list)

    def test_get_all_activities_contains_expected_activities(self, client):
        """Verify response contains known activities."""
        response = client.get("/activities")
        activities = response.json()
        
        expected_activities = [
            "Chess Club",
            "Programming Class",
            "Gym Class",
            "Soccer Team",
            "Basketball Club",
            "Art Club",
            "Music Ensemble",
            "Science Club",
            "Debate Team"
        ]
        
        for activity in expected_activities:
            assert activity in activities


class TestSignupForActivity:
    """Test cases for POST /activities/{activity_name}/signup endpoint."""

    def test_signup_success(self, client):
        """Student successfully signs up for an activity."""
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": "test.student@mergington.edu"}
        )
        assert response.status_code == 200
        assert "Signed up" in response.json()["message"]
        assert "test.student@mergington.edu" in response.json()["message"]

    def test_signup_activity_not_found(self, client):
        """404 error when activity doesn't exist."""
        response = client.post(
            "/activities/Nonexistent Activity/signup",
            params={"email": "test.student@mergington.edu"}
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_signup_already_registered(self, client):
        """400 error when student is already signed up for the activity."""
        # First, get an activity with existing participants
        activities_response = client.get("/activities")
        activities = activities_response.json()
        
        # Find an activity with participants
        for activity_name, activity_data in activities.items():
            if activity_data["participants"]:
                existing_student = activity_data["participants"][0]
                response = client.post(
                    f"/activities/{activity_name}/signup",
                    params={"email": existing_student}
                )
                assert response.status_code == 400
                assert "already signed up" in response.json()["detail"]
                break

    def test_signup_adds_to_participants_list(self, client):
        """Verify email is added to the participants list."""
        activity_name = "Chess Club"
        new_student = "newstudent@mergington.edu"
        
        # Get initial participants
        initial_response = client.get("/activities")
        initial_participants = initial_response.json()[activity_name]["participants"].copy()
        
        # Sign up
        client.post(
            f"/activities/{activity_name}/signup",
            params={"email": new_student}
        )
        
        # Verify student was added
        updated_response = client.get("/activities")
        updated_participants = updated_response.json()[activity_name]["participants"]
        assert new_student in updated_participants
        assert len(updated_participants) == len(initial_participants) + 1


class TestUnregisterFromActivity:
    """Test cases for POST /activities/{activity_name}/unregister endpoint."""

    def test_unregister_success(self, client):
        """Student successfully unregisters from an activity."""
        # First sign up
        activity_name = "Programming Class"
        email = "unreg.test@mergington.edu"
        client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Then unregister
        response = client.post(
            f"/activities/{activity_name}/unregister",
            params={"email": email}
        )
        assert response.status_code == 200
        assert "Removed" in response.json()["message"]
        assert email in response.json()["message"]

    def test_unregister_activity_not_found(self, client):
        """404 error when activity doesn't exist."""
        response = client.post(
            "/activities/Nonexistent Activity/unregister",
            params={"email": "test.student@mergington.edu"}
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_unregister_not_registered(self, client):
        """400 error when student is not signed up for the activity."""
        response = client.post(
            "/activities/Art Club/unregister",
            params={"email": "never.signed.up@mergington.edu"}
        )
        assert response.status_code == 400
        assert "not signed up" in response.json()["detail"]

    def test_unregister_removes_from_participants_list(self, client):
        """Verify email is removed from the participants list."""
        activity_name = "Science Club"
        student_email = "removal.test@mergington.edu"
        
        # Sign up
        client.post(
            f"/activities/{activity_name}/signup",
            params={"email": student_email}
        )
        
        # Verify student was added
        before_unregister = client.get("/activities")
        assert student_email in before_unregister.json()[activity_name]["participants"]
        
        # Unregister
        client.post(
            f"/activities/{activity_name}/unregister",
            params={"email": student_email}
        )
        
        # Verify student was removed
        after_unregister = client.get("/activities")
        assert student_email not in after_unregister.json()[activity_name]["participants"]
