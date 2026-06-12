import pytest


class TestGetActivities:
    """Tests for the GET /activities endpoint"""

    def test_get_activities_returns_all_activities(self, client):
        """Test that GET /activities returns all available activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        activities = response.json()
        assert len(activities) > 0
        assert "Chess Club" in activities
        assert "Programming Class" in activities
        assert "Gym Class" in activities

    def test_activity_structure_has_required_fields(self, client):
        """Test that each activity has the required fields"""
        response = client.get("/activities")
        activities = response.json()
        
        required_fields = {"description", "schedule", "max_participants", "participants"}
        
        for activity_name, activity_data in activities.items():
            assert isinstance(activity_name, str)
            assert isinstance(activity_data, dict)
            assert required_fields.issubset(activity_data.keys()), \
                f"Activity {activity_name} missing required fields"

    def test_activity_participants_is_list(self, client):
        """Test that participants field is a list"""
        response = client.get("/activities")
        activities = response.json()
        
        for activity_name, activity_data in activities.items():
            assert isinstance(activity_data["participants"], list), \
                f"Participants for {activity_name} should be a list"

    def test_activity_has_participants(self, client):
        """Test that activities have at least some participants"""
        response = client.get("/activities")
        activities = response.json()
        
        # Chess Club should have michael@mergington.edu
        assert "michael@mergington.edu" in activities["Chess Club"]["participants"]
        # Programming Class should have emma@mergington.edu
        assert "emma@mergington.edu" in activities["Programming Class"]["participants"]


class TestSignupForActivity:
    """Tests for the POST /activities/{activity_name}/signup endpoint"""

    def test_successful_signup(self, client):
        """Test successful signup for an activity"""
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": "newstudent@mergington.edu"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "newstudent@mergington.edu" in data["message"]
        assert "Chess Club" in data["message"]

    def test_signup_adds_participant_to_activity(self, client):
        """Test that signup actually adds the participant to the activity list"""
        email = "test.participant@mergington.edu"
        activity_name = "Soccer Team"
        
        # Get initial participant count
        get_response = client.get("/activities")
        initial_participants = get_response.json()[activity_name]["participants"].copy()
        
        # Sign up
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        assert response.status_code == 200
        
        # Verify participant was added
        get_response = client.get("/activities")
        updated_participants = get_response.json()[activity_name]["participants"]
        assert email in updated_participants
        assert len(updated_participants) == len(initial_participants) + 1

    def test_signup_nonexistent_activity_returns_404(self, client):
        """Test that signing up for non-existent activity returns 404"""
        response = client.post(
            "/activities/Nonexistent Club/signup",
            params={"email": "student@mergington.edu"}
        )
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]

    def test_signup_duplicate_email_returns_400(self, client):
        """Test that signing up with already registered email returns 400"""
        activity_name = "Chess Club"
        email = "michael@mergington.edu"  # Already signed up
        
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        assert response.status_code == 400
        data = response.json()
        assert "already signed up" in data["detail"]

    def test_signup_different_activity_same_student(self, client):
        """Test that a student can sign up for multiple different activities"""
        email = "versatile.student@mergington.edu"
        
        # Sign up for first activity
        response1 = client.post(
            "/activities/Chess Club/signup",
            params={"email": email}
        )
        assert response1.status_code == 200
        
        # Sign up for second activity
        response2 = client.post(
            "/activities/Programming Class/signup",
            params={"email": email}
        )
        assert response2.status_code == 200
        
        # Verify both signups succeeded
        get_response = client.get("/activities")
        activities = get_response.json()
        assert email in activities["Chess Club"]["participants"]
        assert email in activities["Programming Class"]["participants"]

    def test_signup_case_sensitivity_of_activity_name(self, client):
        """Test that activity names are case-sensitive"""
        response = client.post(
            "/activities/chess club/signup",  # lowercase
            params={"email": "student@mergington.edu"}
        )
        assert response.status_code == 404

    def test_signup_response_message_format(self, client):
        """Test that response message has the correct format"""
        email = "format.test@mergington.edu"
        activity_name = "Art Club"
        
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == f"Signed up {email} for {activity_name}"


class TestRootEndpoint:
    """Tests for the root endpoint"""

    def test_root_redirects_to_static_index(self, client):
        """Test that GET / redirects to /static/index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307  # Temporary redirect
        assert response.headers["location"] == "/static/index.html"

    def test_root_can_follow_redirect(self, client):
        """Test that following the redirect returns static content"""
        response = client.get("/", follow_redirects=True)
        # The response should be either 200 (if static file exists) or 307 if followed
        assert response.status_code in [200, 307]


class TestEdgeCases:
    """Tests for edge cases and special scenarios"""

    def test_multiple_consecutive_signups_same_activity(self, client):
        """Test multiple different students signing up for the same activity"""
        activity_name = "Drama Club"
        emails = [
            "drama.student1@mergington.edu",
            "drama.student2@mergington.edu",
            "drama.student3@mergington.edu"
        ]
        
        for email in emails:
            response = client.post(
                f"/activities/{activity_name}/signup",
                params={"email": email}
            )
            assert response.status_code == 200
        
        # Verify all were added
        get_response = client.get("/activities")
        participants = get_response.json()[activity_name]["participants"]
        for email in emails:
            assert email in participants

    def test_signup_with_special_characters_in_email(self, client):
        """Test signup with email containing special characters"""
        email = "student+tag@mergington.edu"
        response = client.post(
            "/activities/Debate Club/signup",
            params={"email": email}
        )
        # Should succeed - no email validation in the endpoint
        assert response.status_code == 200
        
        # Verify it was added
        get_response = client.get("/activities")
        assert email in get_response.json()["Debate Club"]["participants"]

    def test_all_activities_have_max_participants(self, client):
        """Test that all activities have max_participants field"""
        response = client.get("/activities")
        activities = response.json()
        
        for activity_name, activity_data in activities.items():
            assert "max_participants" in activity_data
            assert isinstance(activity_data["max_participants"], int)
            assert activity_data["max_participants"] > 0

    def test_activities_response_is_dict(self, client):
        """Test that /activities response is a dictionary"""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
