from locust import HttpUser, task, between
import random

# Список тестовых пользователей
test_users = [
    {"email": "test_applicant_0@example.com", "password": "testpass123", "role": "applicant"},
    {"email": "test_moderator_1@example.com", "password": "testpass123", "role": "moderator"},
    {"email": "test_admin_org_2@example.com", "password": "testpass123", "role": "admin_org"},
    {"email": "test_admin_app_3@example.com", "password": "testpass123", "role": "admin_app"},
]

class ApplicantUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        user = random.choice([u for u in test_users if u["role"] == "applicant"])
        response = self.client.post("/api/auth/login/", json={
            "email": user["email"],
            "password": user["password"]
        })
        self.token = response.json().get("access_token")
        self.client.headers.update({"Authorization": f"Bearer {self.token}"})
    @task(3)
    def view_specialties(self):
        self.client.get("/api/org/specialties/")

    @task(1)
    def submit_application(self):
        self.client.post("/api/org/application/", json={
            "specialty_id": 1,
            "organization_id": 1,
            "course": 1,
            "study_form": "full-time"
        })

class ModeratorUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        user = test_users[1]  # Используем moderator
        response = self.client.post("/api/auth/login/", json={
            "email": user["email"],
            "password": user["password"]
        })
        self.token = response.json().get("access_token")
        self.client.headers.update({"Authorization": f"Bearer {self.token}"})

    @task(2)
    def review_applications(self):
        self.client.get("/api/org/applications/")