"""
Edge case tests for the FastAPI Mergington High School Activities API.
Uses the AAA (Arrange-Act-Assert) testing pattern.
"""

import pytest


class TestEdgeCases:
    """Tests for edge cases and boundary conditions"""
    
    def test_signup_multiple_students_same_activity(self, client, reset_activities, test_emails):
        """
        Arrange: Activity has existing participants, new students ready
        Act: Sign up multiple new students to same activity
        Assert: All participants added successfully
        """
        # Arrange
        activity_name = "Programming Class"
        email1 = test_emails["new_student"]
        email2 = test_emails["another_student"]
        
        # Act
        response1 = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email1}
        )
        response2 = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email2}
        )
        
        # Assert
        assert response1.status_code == 200
        assert response2.status_code == 200
        activities_data = client.get("/activities").json()
        participants = activities_data[activity_name]["participants"]
        assert email1 in participants
        assert email2 in participants
        assert len(participants) == 4  # 2 original + 2 new
    
    def test_signup_unregister_signup_cycle(self, client, reset_activities, test_emails):
        """
        Arrange: Student ready
        Act: Sign up, unregister, sign up again multiple times
        Assert: Participant list remains consistent
        """
        # Arrange
        activity_name = "Chess Club"
        email = test_emails["new_student"]
        cycles = 3
        
        # Act & Assert
        for i in range(cycles):
            # Sign up
            signup_response = client.post(
                f"/activities/{activity_name}/signup",
                params={"email": email}
            )
            assert signup_response.status_code == 200
            
            activities_data = client.get("/activities").json()
            assert email in activities_data[activity_name]["participants"]
            
            # Unregister
            delete_response = client.delete(
                f"/activities/{activity_name}/signup",
                params={"email": email}
            )
            assert delete_response.status_code == 200
            
            activities_data = client.get("/activities").json()
            assert email not in activities_data[activity_name]["participants"]
    
    def test_case_sensitive_activity_names(self, client, reset_activities, test_emails):
        """
        Arrange: Activity name with specific casing
        Act: Try signup with lowercase activity name
        Assert: 404 error (case sensitive)
        """
        # Arrange
        activity_name_lower = "chess club"  # lowercase
        email = test_emails["new_student"]
        
        # Act
        response = client.post(
            f"/activities/{activity_name_lower}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 404
    
    def test_special_characters_in_email(self, client, reset_activities):
        """
        Arrange: Email with special characters and URL encoding
        Act: Sign up with special character email
        Assert: Successfully added (handles URL encoding)
        """
        # Arrange
        activity_name = "Chess Club"
        email = "student+test@mergington.edu"  # Email with + character
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 200
        activities_data = client.get("/activities").json()
        assert email in activities_data[activity_name]["participants"]
    
    def test_whitespace_in_requests(self, client, reset_activities):
        """
        Arrange: Email with leading/trailing spaces
        Act: Try signup with whitespace email
        Assert: Email stored as-is (or 400 if validation rejects it)
        """
        # Arrange
        activity_name = "Chess Club"
        email = "  student@mergington.edu  "  # Extra whitespace
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert - Email should be added with whitespace as-is
        assert response.status_code == 200
        activities_data = client.get("/activities").json()
        assert email in activities_data[activity_name]["participants"]
    
    def test_activity_with_max_participants_near_limit(self, client, reset_activities):
        """
        Arrange: Activity with limited spots (max 2, currently has 1)
        Act: Add student to reach limit, then try to add beyond limit
        Assert: Second addition succeeds (no limit enforcement), then fails on duplicate
        """
        # Arrange
        # Create an activity with limited spots for testing
        activities_data = client.get("/activities").json()
        chess_club = activities_data["Chess Club"]
        available_spots = chess_club["max_participants"] - len(chess_club["participants"])
        
        new_email = "limitstudent@mergington.edu"
        activity_name = "Chess Club"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": new_email}
        )
        
        # Assert participant was added
        assert response.status_code == 200
        activities_data = client.get("/activities").json()
        assert new_email in activities_data[activity_name]["participants"]
    
    def test_rapid_delete_operations(self, client, reset_activities, test_emails):
        """
        Arrange: Multiple students in activity
        Act: Delete multiple students rapidly
        Assert: All deletions succeed without interference
        """
        # Arrange
        activity_name = "Chess Club"
        existing_students = ["michael@mergington.edu", "daniel@mergington.edu"]
        
        # Act & Assert
        for email in existing_students:
            response = client.delete(
                f"/activities/{activity_name}/signup",
                params={"email": email}
            )
            assert response.status_code == 200
        
        # Verify all removed
        activities_data = client.get("/activities").json()
        assert len(activities_data[activity_name]["participants"]) == 0
    
    def test_get_activities_after_modifications(self, client, reset_activities, test_emails):
        """
        Arrange: Activity data will be modified
        Act: Perform multiple signups/deletions, then fetch activities
        Assert: GET returns consistent updated data
        """
        # Arrange
        activity_name = "Programming Class"
        email1 = test_emails["new_student"]
        email2 = test_emails["another_student"]
        
        # Act - Signup
        client.post(f"/activities/{activity_name}/signup", params={"email": email1})
        client.post(f"/activities/{activity_name}/signup", params={"email": email2})
        
        # Act - Delete one
        client.delete(f"/activities/{activity_name}/signup", params={"email": email1})
        
        # Act - Fetch
        response = client.get("/activities")
        data = response.json()
        
        # Assert
        assert response.status_code == 200
        participants = data[activity_name]["participants"]
        assert email1 not in participants
        assert email2 in participants
        assert len(participants) == 3  # 2 original + email2


class TestConcurrentLikeOperations:
    """Tests simulating rapid/concurrent operations"""
    
    def test_sequential_signups_different_activities(self, client, reset_activities):
        """
        Arrange: Multiple activities, new student
        Act: Sign up for multiple activities in sequence
        Assert: All signups succeed, participant in all activities
        """
        # Arrange
        email = "multiactivity@mergington.edu"
        activities_list = ["Chess Club", "Programming Class", "Drama Club"]
        
        # Act
        for activity in activities_list:
            response = client.post(
                f"/activities/{activity}/signup",
                params={"email": email}
            )
            assert response.status_code == 200
        
        # Assert
        activities_data = client.get("/activities").json()
        for activity in activities_list:
            assert email in activities_data[activity]["participants"]
    
    def test_interleaved_signup_delete_operations(self, client, reset_activities, test_emails):
        """
        Arrange: Multiple activities and students
        Act: Interleave signup and delete operations
        Assert: All operations succeed without errors
        """
        # Arrange
        email1 = test_emails["new_student"]
        email2 = test_emails["another_student"]
        
        # Act
        # Sign up email1 to Chess Club
        client.post("/activities/Chess Club/signup", params={"email": email1})
        
        # Sign up email2 to Programming Class
        client.post("/activities/Programming Class/signup", params={"email": email2})
        
        # Delete email1 from Chess Club
        response1 = client.delete("/activities/Chess Club/signup", params={"email": email1})
        
        # Sign up email1 to Drama Club
        response2 = client.post("/activities/Drama Club/signup", params={"email": email1})
        
        # Delete email2 from Programming Class
        response3 = client.delete("/activities/Programming Class/signup", params={"email": email2})
        
        # Assert all succeeded
        assert response1.status_code == 200
        assert response2.status_code == 200
        assert response3.status_code == 200
        
        # Verify final state
        activities_data = client.get("/activities").json()
        assert email1 in activities_data["Drama Club"]["participants"]
        assert email1 not in activities_data["Chess Club"]["participants"]
        assert email2 not in activities_data["Programming Class"]["participants"]
