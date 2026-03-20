"""
Tests for the Mergington High School Activities API.

This test suite covers all endpoints with positive and negative test cases
to ensure robust API behavior.
"""

import pytest
from fastapi.testclient import TestClient


class TestActivitiesEndpoint:
    """Tests for GET /activities endpoint."""
    
    def test_get_activities_success(self, client, reset_activities):
        """Test successful retrieval of all activities."""
        response = client.get("/activities")
        
        assert response.status_code == 200
        activities = response.json()
        
        # Verify we get a dictionary
        assert isinstance(activities, dict)
        
        # Verify expected activities are present
        assert "Chess Club" in activities
        assert "Programming Class" in activities
        assert "Gym Class" in activities
        
    def test_get_activities_structure(self, client, reset_activities):
        """Test that activities have the correct structure."""
        response = client.get("/activities")
        activities = response.json()
        
        # Check structure of a sample activity
        chess_club = activities["Chess Club"]
        assert "description" in chess_club
        assert "schedule" in chess_club
        assert "max_participants" in chess_club
        assert "participants" in chess_club
        assert isinstance(chess_club["participants"], list)
        
    def test_get_activities_participants_list(self, client, reset_activities):
        """Test that participants are correctly listed."""
        response = client.get("/activities")
        activities = response.json()
        
        chess_club = activities["Chess Club"]
        assert len(chess_club["participants"]) > 0
        # Verify participants are email strings
        for participant in chess_club["participants"]:
            assert isinstance(participant, str)
            assert "@" in participant


class TestSignupEndpoint:
    """Tests for POST /activities/{activity_name}/signup endpoint."""
    
    def test_signup_success(self, client, reset_activities):
        """Test successful signup for an activity."""
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": "newstudent@mergington.edu"}
        )
        
        assert response.status_code == 200
        result = response.json()
        assert "message" in result
        assert "newstudent@mergington.edu" in result["message"]
        assert "Chess Club" in result["message"]
        
    def test_signup_participant_added(self, client, reset_activities):
        """Test that signup actually adds the participant to the activity."""
        email = "newstudent@mergington.edu"
        
        # Sign up
        client.post(
            "/activities/Chess Club/signup",
            params={"email": email}
        )
        
        # Verify participant was added
        response = client.get("/activities")
        activities = response.json()
        assert email in activities["Chess Club"]["participants"]
        
    def test_signup_activity_not_found(self, client, reset_activities):
        """Test signup fails when activity doesn't exist."""
        response = client.post(
            "/activities/Nonexistent Activity/signup",
            params={"email": "student@mergington.edu"}
        )
        
        assert response.status_code == 404
        result = response.json()
        assert "Activity not found" in result["detail"]
        
    def test_signup_duplicate_email(self, client, reset_activities):
        """Test signup fails when student already registered."""
        email = "michael@mergington.edu"  # Already in Chess Club
        
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": email}
        )
        
        assert response.status_code == 400
        result = response.json()
        assert "already signed up" in result["detail"]
        
    @pytest.mark.parametrize("activity_name,email", [
        ("Programming Class", "new1@mergington.edu"),
        ("Gym Class", "new2@mergington.edu"),
        ("Basketball Team", "new3@mergington.edu"),
    ])
    def test_signup_multiple_activities(self, client, reset_activities, activity_name, email):
        """Test signup works across different activities."""
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        assert response.status_code == 200
        
        # Verify in activities list
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert email in activities[activity_name]["participants"]


class TestRemoveParticipantEndpoint:
    """Tests for DELETE /activities/{activity_name}/participants/{email} endpoint."""
    
    def test_remove_participant_success(self, client, reset_activities):
        """Test successful removal of a participant."""
        email = "michael@mergington.edu"  # Already in Chess Club
        
        response = client.delete(
            f"/activities/Chess Club/participants/{email}"
        )
        
        assert response.status_code == 200
        result = response.json()
        assert "Removed" in result["message"]
        assert email in result["message"]
        
    def test_remove_participant_actually_removed(self, client, reset_activities):
        """Test that removal actually removes the participant."""
        email = "michael@mergington.edu"
        
        # Remove participant
        client.delete(f"/activities/Chess Club/participants/{email}")
        
        # Verify removed
        response = client.get("/activities")
        activities = response.json()
        assert email not in activities["Chess Club"]["participants"]
        
    def test_remove_participant_activity_not_found(self, client, reset_activities):
        """Test removal fails when activity doesn't exist."""
        response = client.delete(
            "/activities/Nonexistent Activity/participants/student@mergington.edu"
        )
        
        assert response.status_code == 404
        result = response.json()
        assert "Activity not found" in result["detail"]
        
    def test_remove_participant_not_found(self, client, reset_activities):
        """Test removal fails when participant not in activity."""
        response = client.delete(
            "/activities/Chess Club/participants/notinlist@mergington.edu"
        )
        
        assert response.status_code == 404
        result = response.json()
        assert "Participant not found" in result["detail"]
        
    def test_remove_participant_with_special_characters_in_email(self, client, reset_activities):
        """Test removal works with special characters in email."""
        email = "student+tag@mergington.edu"
        
        # First add the participant
        client.post(
            "/activities/Chess Club/signup",
            params={"email": email}
        )
        
        # Then remove
        response = client.delete(
            f"/activities/Chess Club/participants/{email}"
        )
        
        assert response.status_code == 200


class TestRootEndpoint:
    """Tests for GET / endpoint."""
    
    def test_root_redirect(self, client, reset_activities):
        """Test that root endpoint redirects to static index."""
        response = client.get("/", follow_redirects=False)
        
        # Should redirect (status code 307 or similar)
        assert response.status_code in [307, 308]
        assert "/static/index.html" in response.headers.get("location", "")
        
    def test_root_redirect_follow(self, client, reset_activities):
        """Test following the redirect from root endpoint."""
        response = client.get("/", follow_redirects=True)
        
        # After following redirect, should get the static file
        # (TestClient will get 200 if the file is served)
        assert response.status_code == 200


class TestIntegration:
    """Integration tests covering multiple endpoints together."""
    
    def test_signup_then_remove_workflow(self, client, reset_activities):
        """Test complete workflow: signup and then remove a participant."""
        email = "integration@mergington.edu"
        activity = "Chess Club"
        
        # Initially, email should not be in Chess Club
        response = client.get("/activities")
        activities = response.json()
        assert email not in activities[activity]["participants"]
        
        # Sign up
        signup_response = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        assert signup_response.status_code == 200
        
        # Verify added
        response = client.get("/activities")
        activities = response.json()
        assert email in activities[activity]["participants"]
        
        # Remove
        remove_response = client.delete(
            f"/activities/{activity}/participants/{email}"
        )
        assert remove_response.status_code == 200
        
        # Verify removed
        response = client.get("/activities")
        activities = response.json()
        assert email not in activities[activity]["participants"]
        
    def test_multiple_signups_then_remove_one(self, client, reset_activities):
        """Test signing up multiple participants and removing one."""
        activity = "Programming Class"
        emails = ["user1@mergington.edu", "user2@mergington.edu", "user3@mergington.edu"]
        
        # Sign up all
        for email in emails:
            client.post(
                f"/activities/{activity}/signup",
                params={"email": email}
            )
        
        # Verify all added
        response = client.get("/activities")
        activities = response.json()
        for email in emails:
            assert email in activities[activity]["participants"]
        
        # Remove middle one
        client.delete(f"/activities/{activity}/participants/{emails[1]}")
        
        # Verify correct one removed
        response = client.get("/activities")
        activities = response.json()
        assert emails[0] in activities[activity]["participants"]
        assert emails[1] not in activities[activity]["participants"]
        assert emails[2] in activities[activity]["participants"]
