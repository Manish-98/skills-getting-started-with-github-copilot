"""
Tests for the FastAPI Mergington High School Activities API.
Uses the AAA (Arrange-Act-Assert) testing pattern.
"""

import pytest


class TestGetActivities:
    """Tests for GET /activities endpoint"""
    
    def test_get_all_activities_returns_success(self, client, reset_activities):
        """
        Arrange: Client is ready
        Act: GET /activities
        Assert: Returns 200 and all activities
        """
        # Arrange
        # (client and reset_activities fixtures ready)
        
        # Act
        response = client.get("/activities")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 9  # All 9 activities present
    
    def test_get_activities_response_structure(self, client, reset_activities):
        """
        Arrange: Client is ready
        Act: GET /activities
        Assert: Response has correct structure for each activity
        """
        # Arrange
        # (fixtures ready)
        
        # Act
        response = client.get("/activities")
        data = response.json()
        
        # Assert
        for activity_name, activity_data in data.items():
            assert isinstance(activity_name, str)
            assert "description" in activity_data
            assert "schedule" in activity_data
            assert "max_participants" in activity_data
            assert isinstance(activity_data["max_participants"], int)
            assert "participants" in activity_data
            assert isinstance(activity_data["participants"], list)
    
    def test_get_activities_includes_existing_participants(self, client, reset_activities):
        """
        Arrange: Initial data has participants in Chess Club
        Act: GET /activities
        Assert: Chess Club contains expected participants
        """
        # Arrange
        # (reset_activities fixture sets up initial data)
        
        # Act
        response = client.get("/activities")
        data = response.json()
        chess_club = data["Chess Club"]
        
        # Assert
        assert "michael@mergington.edu" in chess_club["participants"]
        assert "daniel@mergington.edu" in chess_club["participants"]
        assert len(chess_club["participants"]) == 2


class TestPostSignup:
    """Tests for POST /activities/{activity_name}/signup endpoint"""
    
    def test_signup_new_student_succeeds(self, client, reset_activities, test_emails):
        """
        Arrange: New student email, existing activity
        Act: POST signup for that student
        Assert: 200, success message, participant added
        """
        # Arrange
        activity_name = "Chess Club"
        email = test_emails["new_student"]
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert email in data["message"]
        assert activity_name in data["message"]
        
        # Verify participant was added
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert email in activities_data[activity_name]["participants"]
    
    def test_signup_multiple_students_different_activities(self, client, reset_activities, test_emails):
        """
        Arrange: Two new students, two different activities
        Act: Sign up both students
        Assert: Both signups succeed
        """
        # Arrange
        student1_email = test_emails["new_student"]
        student2_email = test_emails["another_student"]
        activity1 = "Chess Club"
        activity2 = "Programming Class"
        
        # Act
        response1 = client.post(
            f"/activities/{activity1}/signup",
            params={"email": student1_email}
        )
        response2 = client.post(
            f"/activities/{activity2}/signup",
            params={"email": student2_email}
        )
        
        # Assert
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        # Verify both were added
        activities_response = client.get("/activities")
        data = activities_response.json()
        assert student1_email in data[activity1]["participants"]
        assert student2_email in data[activity2]["participants"]
    
    def test_signup_duplicate_student_returns_400(self, client, reset_activities, test_emails):
        """
        Arrange: Student already in Chess Club
        Act: Try to sign up same student again
        Assert: 400 error with appropriate message
        """
        # Arrange
        activity_name = "Chess Club"
        email = test_emails["existing_student"]  # michael@mergington.edu
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 400
        data = response.json()
        assert "already signed up" in data["detail"].lower()
    
    def test_signup_nonexistent_activity_returns_404(self, client, reset_activities, test_emails, test_activities_names):
        """
        Arrange: Activity doesn't exist
        Act: Try to sign up for nonexistent activity
        Assert: 404 error with appropriate message
        """
        # Arrange
        activity_name = test_activities_names["nonexistent"]
        email = test_emails["new_student"]
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()


class TestDeleteSignup:
    """Tests for DELETE /activities/{activity_name}/signup endpoint"""
    
    def test_delete_signup_existing_student_succeeds(self, client, reset_activities, test_emails):
        """
        Arrange: Student already signed up for Chess Club
        Act: DELETE signup for that student
        Assert: 200, success message, participant removed
        """
        # Arrange
        activity_name = "Chess Club"
        email = test_emails["existing_student"]  # michael@mergington.edu
        
        # Verify student is there before
        activities_before = client.get("/activities").json()
        assert email in activities_before[activity_name]["participants"]
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "Unregistered" in data["message"]
        
        # Verify participant was removed
        activities_after = client.get("/activities").json()
        assert email not in activities_after[activity_name]["participants"]
    
    def test_delete_signup_student_not_signed_up_returns_400(self, client, reset_activities, test_emails):
        """
        Arrange: Student not signed up for activity
        Act: Try to delete signup for that student
        Assert: 400 error with appropriate message
        """
        # Arrange
        activity_name = "Chess Club"
        email = test_emails["new_student"]  # Not in Chess Club
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 400
        data = response.json()
        assert "not signed up" in data["detail"].lower()
    
    def test_delete_signup_nonexistent_activity_returns_404(self, client, reset_activities, test_emails, test_activities_names):
        """
        Arrange: Activity doesn't exist
        Act: Try to delete signup from nonexistent activity
        Assert: 404 error with appropriate message
        """
        # Arrange
        activity_name = test_activities_names["nonexistent"]
        email = test_emails["new_student"]
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()
    
    def test_delete_then_signup_again_succeeds(self, client, reset_activities, test_emails):
        """
        Arrange: Student is signed up
        Act: Delete signup, then sign up again
        Assert: Both operations succeed
        """
        # Arrange
        activity_name = "Chess Club"
        email = test_emails["existing_student"]
        
        # Act - Delete
        delete_response = client.delete(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert delete succeeded
        assert delete_response.status_code == 200
        
        # Act - Signup again
        signup_response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert signup succeeded
        assert signup_response.status_code == 200
        activities_data = client.get("/activities").json()
        assert email in activities_data[activity_name]["participants"]


class TestIntegrationScenarios:
    """Integration tests combining multiple operations"""
    
    def test_full_signup_workflow(self, client, reset_activities, test_emails):
        """
        Arrange: New student ready to sign up
        Act: Sign up student, verify in list, then remove
        Assert: All operations succeed in sequence
        """
        # Arrange
        activity_name = "Programming Class"
        email = test_emails["new_student"]
        
        # Act 1 - Signup
        signup_response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        assert signup_response.status_code == 200
        
        # Act 2 - Verify in list
        activities_data = client.get("/activities").json()
        assert email in activities_data[activity_name]["participants"]
        
        # Act 3 - Remove from activity
        delete_response = client.delete(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        assert delete_response.status_code == 200
        
        # Assert - Verify removed
        activities_data = client.get("/activities").json()
        assert email not in activities_data[activity_name]["participants"]
