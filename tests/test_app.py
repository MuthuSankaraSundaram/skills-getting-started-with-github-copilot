import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add src directory to path so we can import app
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import app

client = TestClient(app)


class TestGetActivities:
    """Tests for the GET /activities endpoint"""

    def test_get_activities_returns_200(self):
        """Test that the activities endpoint returns a 200 status code"""
        response = client.get("/activities")
        assert response.status_code == 200

    def test_get_activities_returns_dict(self):
        """Test that the activities endpoint returns a dictionary"""
        response = client.get("/activities")
        assert isinstance(response.json(), dict)

    def test_get_activities_contains_chess_club(self):
        """Test that activities include Chess Club"""
        response = client.get("/activities")
        activities = response.json()
        assert "Chess Club" in activities

    def test_get_activities_has_required_fields(self):
        """Test that each activity has required fields"""
        response = client.get("/activities")
        activities = response.json()
        
        for activity_name, activity_details in activities.items():
            assert "description" in activity_details
            assert "schedule" in activity_details
            assert "max_participants" in activity_details
            assert "participants" in activity_details
            assert isinstance(activity_details["participants"], list)

    def test_get_activities_count(self):
        """Test that there are activities in the list"""
        response = client.get("/activities")
        activities = response.json()
        assert len(activities) > 0


class TestSignupForActivity:
    """Tests for the POST /activities/{activity_name}/signup endpoint"""

    def test_signup_for_activity_returns_201_or_200(self):
        """Test that signup returns a success status code"""
        response = client.post(
            "/activities/Chess%20Club/signup?email=test@mergington.edu"
        )
        assert response.status_code in [200, 201]

    def test_signup_new_student(self):
        """Test signing up a new student"""
        email = "newstudent@mergington.edu"
        response = client.post(
            f"/activities/Chess%20Club/signup?email={email}"
        )
        assert response.status_code == 200
        assert "Signed up" in response.json()["message"]

    def test_signup_duplicate_fails(self):
        """Test that signing up twice fails with 400"""
        email = "duplicate@mergington.edu"
        # First signup should succeed
        response1 = client.post(
            f"/activities/Programming%20Class/signup?email={email}"
        )
        assert response1.status_code == 200
        
        # Second signup with same email should fail
        response2 = client.post(
            f"/activities/Programming%20Class/signup?email={email}"
        )
        assert response2.status_code == 400
        assert "already signed up" in response2.json()["detail"]

    def test_signup_for_nonexistent_activity(self):
        """Test that signing up for nonexistent activity returns 404"""
        response = client.post(
            "/activities/Nonexistent%20Activity/signup?email=test@mergington.edu"
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_signup_updates_participant_list(self):
        """Test that signup updates the participant list"""
        email = "newsignup@mergington.edu"
        
        # Get initial count
        response1 = client.get("/activities")
        initial_count = len(response1.json()["Soccer Team"]["participants"])
        
        # Sign up
        client.post(f"/activities/Soccer%20Team/signup?email={email}")
        
        # Get updated count
        response2 = client.get("/activities")
        updated_count = len(response2.json()["Soccer Team"]["participants"])
        
        assert updated_count == initial_count + 1
        assert email in response2.json()["Soccer Team"]["participants"]


class TestUnregisterFromActivity:
    """Tests for the POST /activities/{activity_name}/unregister endpoint"""

    def test_unregister_returns_200(self):
        """Test that unregister returns a 200 status code"""
        # First signup
        email = "unregister_test@mergington.edu"
        client.post(f"/activities/Basketball%20Club/signup?email={email}")
        
        # Then unregister
        response = client.post(
            f"/activities/Basketball%20Club/unregister?email={email}"
        )
        assert response.status_code == 200
        assert "Unregistered" in response.json()["message"]

    def test_unregister_removes_participant(self):
        """Test that unregister removes the participant from the list"""
        email = "unregister_remove@mergington.edu"
        
        # Sign up
        client.post(f"/activities/Art%20Club/signup?email={email}")
        
        # Verify signup
        response1 = client.get("/activities")
        assert email in response1.json()["Art Club"]["participants"]
        
        # Unregister
        client.post(f"/activities/Art%20Club/unregister?email={email}")
        
        # Verify removal
        response2 = client.get("/activities")
        assert email not in response2.json()["Art Club"]["participants"]

    def test_unregister_nonexistent_participant_fails(self):
        """Test that unregistering a non-participant returns 400"""
        response = client.post(
            "/activities/Drama%20Club/unregister?email=notregistered@mergington.edu"
        )
        assert response.status_code == 400
        assert "not signed up" in response.json()["detail"]

    def test_unregister_from_nonexistent_activity_fails(self):
        """Test that unregistering from nonexistent activity returns 404"""
        response = client.post(
            "/activities/Nonexistent%20Activity/unregister?email=test@mergington.edu"
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_unregister_then_signup_again(self):
        """Test that a student can signup again after unregistering"""
        email = "reregister@mergington.edu"
        activity = "Photography%20Club"
        
        # First signup
        client.post(f"/activities/{activity}/signup?email={email}")
        
        # Unregister
        client.post(f"/activities/{activity}/unregister?email={email}")
        
        # Signup again - should succeed
        response = client.post(f"/activities/{activity}/signup?email={email}")
        assert response.status_code == 200


class TestRootEndpoint:
    """Tests for the root endpoint"""

    def test_root_redirects(self):
        """Test that root endpoint redirects to static page"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307  # Temporary redirect
        assert "/static/index.html" in response.headers["location"]
