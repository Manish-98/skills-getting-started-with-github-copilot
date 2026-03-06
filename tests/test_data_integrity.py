"""
Data integrity tests for the FastAPI Mergington High School Activities API.
Uses the AAA (Arrange-Act-Assert) testing pattern.
"""

import pytest


class TestDataIntegrity:
    """Tests for data consistency and integrity"""
    
    def test_participant_list_structure_after_signup(self, client, reset_activities, test_emails):
        """
        Arrange: Activity with participants
        Act: Add new participant
        Assert: Participants list is valid list of emails
        """
        # Arrange
        activity_name = "Chess Club"
        email = test_emails["new_student"]
        
        # Act
        client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        activities_data = client.get("/activities").json()
        participants = activities_data[activity_name]["participants"]
        assert isinstance(participants, list)
        assert all(isinstance(p, str) for p in participants)
        assert email in participants
    
    def test_no_duplicate_participants_after_operations(self, client, reset_activities, test_emails):
        """
        Arrange: Activity with existing participants
        Act: Sign up, delete, sign up again
        Assert: No duplicates in participant list
        """
        # Arrange
        activity_name = "Chess Club"
        email = test_emails["new_student"]
        
        # Act - Sign up
        client.post(f"/activities/{activity_name}/signup", params={"email": email})
        
        # Assert no duplicates yet
        activities_data = client.get("/activities").json()
        participants = activities_data[activity_name]["participants"]
        assert participants.count(email) == 1
        
        # Act - Delete and sign up again
        client.delete(f"/activities/{activity_name}/signup", params={"email": email})
        client.post(f"/activities/{activity_name}/signup", params={"email": email})
        
        # Assert still no duplicates
        activities_data = client.get("/activities").json()
        participants = activities_data[activity_name]["participants"]
        assert participants.count(email) == 1
    
    def test_activity_metadata_unchanged_after_modifications(self, client, reset_activities):
        """
        Arrange: Activity with metadata
        Act: Add/remove participants
        Assert: Description, schedule, max_participants unchanged
        """
        # Arrange
        activity_name = "Chess Club"
        activities_data = client.get("/activities").json()
        original_activity = activities_data[activity_name]
        original_description = original_activity["description"]
        original_schedule = original_activity["schedule"]
        original_max = original_activity["max_participants"]
        
        # Act - Add participant
        client.post(
            f"/activities/{activity_name}/signup",
            params={"email": "test@mergington.edu"}
        )
        
        # Act - Remove participant
        client.delete(
            f"/activities/{activity_name}/signup",
            params={"email": "michael@mergington.edu"}
        )
        
        # Assert metadata unchanged
        activities_data = client.get("/activities").json()
        modified_activity = activities_data[activity_name]
        assert modified_activity["description"] == original_description
        assert modified_activity["schedule"] == original_schedule
        assert modified_activity["max_participants"] == original_max
    
    def test_participant_count_accuracy_after_signup(self, client, reset_activities, test_emails):
        """
        Arrange: Activity with known participant count
        Act: Sign up new participant
        Assert: Count incremented by exactly 1
        """
        # Arrange
        activity_name = "Programming Class"
        activities_data = client.get("/activities").json()
        original_count = len(activities_data[activity_name]["participants"])
        
        email = test_emails["new_student"]
        
        # Act
        client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        activities_data = client.get("/activities").json()
        new_count = len(activities_data[activity_name]["participants"])
        assert new_count == original_count + 1
    
    def test_participant_count_accuracy_after_delete(self, client, reset_activities):
        """
        Arrange: Activity with known participant count
        Act: Remove participant
        Assert: Count decremented by exactly 1
        """
        # Arrange
        activity_name = "Chess Club"
        activities_data = client.get("/activities").json()
        original_count = len(activities_data[activity_name]["participants"])
        
        email_to_remove = "michael@mergington.edu"
        
        # Act
        client.delete(
            f"/activities/{activity_name}/signup",
            params={"email": email_to_remove}
        )
        
        # Assert
        activities_data = client.get("/activities").json()
        new_count = len(activities_data[activity_name]["participants"])
        assert new_count == original_count - 1
    
    def test_all_activities_present_after_modifications(self, client, reset_activities):
        """
        Arrange: All activities exist
        Act: Modify participants across multiple activities
        Assert: All 9 activities still present
        """
        # Arrange
        activity_count = 9
        
        # Act - Perform various modifications
        client.post("/activities/Chess Club/signup", params={"email": "test1@mergington.edu"})
        client.delete("/activities/Basketball Team/signup", params={"email": "james@mergington.edu"})
        client.post("/activities/Art Studio/signup", params={"email": "test2@mergington.edu"})
        
        # Assert
        activities_data = client.get("/activities").json()
        assert len(activities_data) == activity_count
        assert "Chess Club" in activities_data
        assert "Programming Class" in activities_data
        assert "Drama Club" in activities_data
    
    def test_specific_participant_email_persists_after_other_operations(self, client, reset_activities):
        """
        Arrange: Participant in activity
        Act: Add/remove other participants from other activities
        Assert: Original participant still there
        """
        # Arrange
        activity_name = "Chess Club"
        specific_email = "michael@mergington.edu"
        
        # Verify they're there
        activities_data = client.get("/activities").json()
        assert specific_email in activities_data[activity_name]["participants"]
        
        # Act - Modify other activities
        client.post("/activities/Drama Club/signup", params={"email": "outsider@mergington.edu"})
        client.delete("/activities/Basketball Team/signup", params={"email": "james@mergington.edu"})
        
        # Assert specific participant still there
        activities_data = client.get("/activities").json()
        assert specific_email in activities_data[activity_name]["participants"]


class TestDataConsistency:
    """Tests for data consistency across operations"""
    
    def test_email_format_consistency(self, client, reset_activities):
        """
        Arrange: Various email formats
        Act: Add emails to system
        Assert: Emails stored in exact format provided
        """
        # Arrange
        activity_name = "Chess Club"
        emails = [
            "test@mergington.edu",
            "student+1@mergington.edu",
            "john.doe@mergington.edu"
        ]
        
        # Act
        for email in emails:
            client.post(
                f"/activities/{activity_name}/signup",
                params={"email": email}
            )
        
        # Assert
        activities_data = client.get("/activities").json()
        participants = activities_data[activity_name]["participants"]
        for email in emails:
            assert email in participants
    
    def test_removal_only_affects_target_participant(self, client, reset_activities):
        """
        Arrange: Multiple participants in activity
        Act: Remove one specific participant
        Assert: Only that participant removed, others unchanged
        """
        # Arrange
        activity_name = "Chess Club"
        original_participants = ["michael@mergington.edu", "daniel@mergington.edu"]
        email_to_remove = "michael@mergington.edu"
        
        # Verify initial state
        activities_data = client.get("/activities").json()
        assert all(p in activities_data[activity_name]["participants"] for p in original_participants)
        
        # Act
        client.delete(
            f"/activities/{activity_name}/signup",
            params={"email": email_to_remove}
        )
        
        # Assert
        activities_data = client.get("/activities").json()
        participants = activities_data[activity_name]["participants"]
        assert email_to_remove not in participants
        assert "daniel@mergington.edu" in participants
    
    def test_addition_only_affects_target_activity(self, client, reset_activities):
        """
        Arrange: Multiple activities exist
        Act: Add participant to one activity
        Assert: Only that activity affected
        """
        # Arrange
        email = "new@mergington.edu"
        target_activity = "Chess Club"
        other_activity = "Drama Club"
        
        # Get initial states
        activities_before = client.get("/activities").json()
        drama_participants_before = activities_before[other_activity]["participants"].copy()
        
        # Act
        client.post(
            f"/activities/{target_activity}/signup",
            params={"email": email}
        )
        
        # Assert
        activities_after = client.get("/activities").json()
        assert email in activities_after[target_activity]["participants"]
        # Drama Club participants should be unchanged
        assert activities_after[other_activity]["participants"] == drama_participants_before
