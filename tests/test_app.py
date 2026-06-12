import pytest


class TestGetActivities:
    """Tests for the GET /activities endpoint"""

    def test_get_activities_returns_all_activities(self, client):
        """Test that GET /activities returns all available activities"""
        # Arrange
        expected_activities = ["Chess Club", "Programming Class", "Gym Class"]

        # Act
        response = client.get("/activities")
        activities = response.json()

        # Assert
        assert response.status_code == 200
        assert len(activities) > 0
        for activity in expected_activities:
            assert activity in activities

    def test_activity_structure_has_required_fields(self, client):
        """Test that each activity has the required fields"""
        # Arrange
        required_fields = {"description", "schedule", "max_participants", "participants"}

        # Act
        response = client.get("/activities")
        activities = response.json()

        # Assert
        for activity_name, activity_data in activities.items():
            assert isinstance(activity_name, str), f"Activity name '{activity_name}' should be a string"
            assert isinstance(activity_data, dict), f"Activity data for '{activity_name}' should be a dictionary"
            assert required_fields.issubset(activity_data.keys()),                 f"Activity '{activity_name}' missing required fields"

    def test_activity_participants_is_list(self, client):
        """Test that participants field is a list"""
        # Arrange & Act
        response = client.get("/activities")
        activities = response.json()

        # Assert
        for activity_name, activity_data in activities.items():
            assert isinstance(activity_data["participants"], list),                 f"Participants for '{activity_name}' should be a list"

    def test_activity_has_participants(self, client):
        """Test that activities have at least some participants"""
        # Arrange
        expected_participants = {
            "Chess Club": "michael@mergington.edu",
            "Programming Class": "emma@mergington.edu"
        }

        # Act
        response = client.get("/activities")
        activities = response.json()

        # Assert
        for activity_name, expected_email in expected_participants.items():
            assert expected_email in activities[activity_name]["participants"],                 f"Expected {expected_email} in {activity_name} participants"


class TestSignupForActivity:
    """Tests for the POST /activities/{activity_name}/signup endpoint"""

    def test_successful_signup(self, client):
        """Test successful signup for an activity"""
        # Arrange
        activity_name = "Chess Club"
        email = "newstudent@mergington.edu"

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

    def test_signup_adds_participant_to_activity(self, client):
        """Test that signup actually adds the participant to the activity list"""
        # Arrange
        email = "test.participant@mergington.edu"
        activity_name = "Soccer Team"
        get_response = client.get("/activities")
        initial_participants = get_response.json()[activity_name]["participants"].copy()
        initial_count = len(initial_participants)

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )

        # Assert
        assert response.status_code == 200
        get_response = client.get("/activities")
        updated_participants = get_response.json()[activity_name]["participants"]
        assert email in updated_participants
        assert len(updated_participants) == initial_count + 1

    def test_signup_nonexistent_activity_returns_404(self, client):
        """Test that signing up for non-existent activity returns 404"""
        # Arrange
        activity_name = "Nonexistent Club"
        email = "student@mergington.edu"

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]

    def test_signup_duplicate_email_returns_400(self, client):
        """Test that signing up with already registered email returns 400"""
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )

        # Assert
        assert response.status_code == 400
        data = response.json()
        assert "already signed up" in data["detail"]

    def test_signup_different_activity_same_student(self, client):
        """Test that a student can sign up for multiple different activities"""
        # Arrange
        email = "versatile.student@mergington.edu"
        activities = ["Chess Club", "Programming Class"]

        # Act
        responses = []
        for activity_name in activities:
            response = client.post(
                f"/activities/{activity_name}/signup",
                params={"email": email}
            )
            responses.append(response)

        # Assert
        assert all(r.status_code == 200 for r in responses)
        get_response = client.get("/activities")
        activities_data = get_response.json()
        assert email in activities_data["Chess Club"]["participants"]
        assert email in activities_data["Programming Class"]["participants"]

    def test_signup_case_sensitivity_of_activity_name(self, client):
        """Test that activity names are case-sensitive"""
        # Arrange
        activity_name = "chess club"
        email = "student@mergington.edu"

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )

        # Assert
        assert response.status_code == 404

    def test_signup_response_message_format(self, client):
        """Test that response message has the correct format"""
        # Arrange
        activity_name = "Art Club"
        email = "format.test@mergington.edu"
        expected_message = f"Signed up {email} for {activity_name}"

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == expected_message


class TestRootEndpoint:
    """Tests for the root endpoint"""

    def test_root_redirects_to_static_index(self, client):
        """Test that GET / redirects to /static/index.html"""
        # Arrange
        expected_location = "/static/index.html"

        # Act
        response = client.get("/", follow_redirects=False)

        # Assert
        assert response.status_code == 307
        assert response.headers["location"] == expected_location

    def test_root_can_follow_redirect(self, client):
        """Test that following the redirect returns static content"""
        # Arrange
        valid_status_codes = [200, 307]

        # Act
        response = client.get("/", follow_redirects=True)

        # Assert
        assert response.status_code in valid_status_codes


class TestEdgeCases:
    """Tests for edge cases and special scenarios"""

    def test_multiple_consecutive_signups_same_activity(self, client):
        """Test multiple different students signing up for the same activity"""
        # Arrange
        activity_name = "Drama Club"
        emails = [
            "drama.student1@mergington.edu",
            "drama.student2@mergington.edu",
            "drama.student3@mergington.edu"
        ]

        # Act
        responses = []
        for email in emails:
            response = client.post(
                f"/activities/{activity_name}/signup",
                params={"email": email}
            )
            responses.append(response)

        # Assert
        assert all(r.status_code == 200 for r in responses)
        get_response = client.get("/activities")
        participants = get_response.json()[activity_name]["participants"]
        for email in emails:
            assert email in participants

    def test_signup_with_special_characters_in_email(self, client):
        """Test signup with email containing special characters"""
        # Arrange
        email = "student+tag@mergington.edu"
        activity_name = "Debate Club"

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )

        # Assert
        assert response.status_code == 200
        get_response = client.get("/activities")
        assert email in get_response.json()[activity_name]["participants"]

    def test_all_activities_have_max_participants(self, client):
        """Test that all activities have max_participants field"""
        # Arrange
        expected_field = "max_participants"

        # Act
        response = client.get("/activities")
        activities = response.json()

        # Assert
        for activity_name, activity_data in activities.items():
            assert expected_field in activity_data
            assert isinstance(activity_data[expected_field], int)
            assert activity_data[expected_field] > 0

    def test_activities_response_is_dict(self, client):
        """Test that /activities response is a dictionary"""
        # Arrange
        expected_type = dict

        # Act
        response = client.get("/activities")
        data = response.json()

        # Assert
        assert response.status_code == 200
        assert isinstance(data, expected_type)
