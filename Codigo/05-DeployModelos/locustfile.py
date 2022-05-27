from locust import HttpUser, between, task
class WebsiteUser(HttpUser):
    wait_time = between(5, 15)

    @task
    def test_2(self):
        self.client.get("/predecir?dato=0.4")
        
    #@task
    #def test(self):
    #w    self.client.get("/unit_tests")
