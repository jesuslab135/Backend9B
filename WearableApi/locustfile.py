from locust import HttpUser, task

class MiUsuario(HttpUser):
    @task
    def visitar_home(self):
        self.client.get("/")

