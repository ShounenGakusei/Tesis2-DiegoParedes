from locust import HttpUser, between, task
class WebsiteUser(HttpUser):
    #wait_time = between(1, 6000)

    @task(10)
    def test_2(self):
        self.client.get("/predecir?dato=0.4")
        
    #@task(1)
    def test1(self):
        self.client.get("/predecir?dato=0.4&fecha=2022-01-31-12-00")

    #@task(1)
    def test2(self):
        self.client.get("/predecir?dato=0.4&fecha=2022-01-31-14-00")

    #@task(1)
    def test3(self):
        self.client.get("/predecir?dato=0.4&fecha=2022-01-31-16-00")