import re
import requests
import urllib3
from bs4 import BeautifulSoup
from controllers.actions import (save_user,
                                 get_user_by_email,
                                 get_all_users)

BASE_URL = 'https://www.cnpja.com'
RETOOL_URL = 'https://cnpja.retool.com/api'
URL_ID = '2f1a91f8-bd0c-427f-8732-ce280b2a71fc'
URL_API = 'https://api.cnpja.com'


class Browser(object):

    def __init__(self):
        self.response = None
        self.headers = self.get_headers()
        self.session = requests.Session()

    def get_headers(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/87.0.4280.88 Safari/537.36"
        }
        return self.headers

    def send_request(self, method, url, **kwargs):
        urllib3.disable_warnings()
        self.response = self.session.request(method, url, **kwargs)
        return self.response


class CnpjAPI(Browser):

    def __init__(self, email='pycnpj@gmail.com', password='PyCnpj2023?'):
        super().__init__()
        self.base_email = email
        self.password = password
        self.current_email = email
        self.document = None
        self.state = "ES"
        self.mounted_url_login = None
        self.url_login = None
        self.url_signup = None
        self.auth_token = None
        self.api_key = None

    def accounts_manager(self):
        users = get_all_users()
        count = 0
        profile = None
        if users.get("result"):
            for user in users["object"]:
                self.api_key = user.get("api_key")
                remaining_credits = self.check_credits()
                if remaining_credits.get("perpetual", 0) > 0:
                    user["credits"] = remaining_credits
                    print("Usando conta existente: ", user)
                    return user
            count += users["object"][-1]["id"] + 1
        self.current_email = f"{self.base_email.split('@')[0]}+{count}@{self.base_email.split('@')[1]}"
        user = self.authenticate()
        if user.get("status", "NOT_FOUND") in ["ACTIVED", "PENDING"]:
            profile = self.get_user_profile()
        self.create_account()
        return profile

    def check_credits(self):
        self.headers["Authorization"] = self.api_key
        self.response = self.send_request('GET',
                                          f"{URL_API}/credit",
                                          headers=self.headers)
        return self.response.json()

    def create_account(self):
        profile = None
        user_data = get_user_by_email(self.current_email)
        if not user_data.get("result"):
            print("Criando nova conta com email: ", self.current_email)
            self.mount_url_login()

            self.headers["Referer"] = f"{BASE_URL}/"
            signup_url = self.send_request('GET',
                                           self.url_login.replace("login", "signup"),
                                           headers=self.headers).url

            self.headers = self.get_headers()
            data = {
                "state": self.url_login.split("=")[1],
                "strengthPolicy": "good",
                "complexityOptions.minLength": 8,
                "email": self.current_email,
                "password": self.password,
                "action": 'default'
            }
            self.headers["Origin"] = "https://cnpja.auth0.com"
            self.headers["Referer"] = self.url_login.replace("login", "signup")
            self.send_request('POST', signup_url, data=data, headers=self.headers)
            user = self.authenticate()
            if user.get("status") in ["ACTIVED", "PENDING"]:
                profile = self.get_user_profile()
        return profile

    def signup_with_google(self):
        self.mount_url_login()

        self.headers["Referer"] = f"{BASE_URL}/"
        self.send_request('GET',
                          self.url_login,
                          headers=self.headers)

        self.headers = self.get_headers()
        data = {
            "state": self.url_login.split("=")[1],
            "connection": 'google-oauth2'
        }
        self.headers["Origin"] = "https://cnpja.auth0.com"
        self.headers["Referer"] = self.url_login
        url_auth_location = self.send_request('POST',
                                              self.url_login,
                                              data=data,
                                              headers=self.headers)
        print(url_auth_location.url)

    def get_token(self):
        data = {
            "username": self.current_email,
            "password": self.password
        }
        self.auth_token = self.send_request('POST',
                                            f"{URL_API}/auth",
                                            json=data,
                                            headers=self.headers).json()['idToken']
        return self.auth_token

    def authenticate(self):
        self.url_login = self.mount_url_login()
        status = "ACTIVED"
        data = {
            "state": self.url_login.split("=")[1],
            "username": self.current_email,
            "password": self.password,
            "action": "default"
        }
        self.headers["Origin"] = "https://cnpja.auth0.com"
        self.headers["Referer"] = self.url_login
        url_auth = self.send_request('POST',
                                     self.url_login,
                                     data=data)
        try:
            self.auth_token = re.findall("id_token=(.*?)$", url_auth.url)[0]
        except:
            status = "SUSPENDED" if "login" not in url_auth.url else "PENDING"
        return {"status": status}

    def get_user_profile(self):
        self.headers = self.get_headers()
        self.headers["Origin"] = "https://www.cnpja.com"
        self.headers["referer"] = "https://www.cnpja.com/"
        self.headers["authorization"] = f"Bearer {self.auth_token}"
        response = self.send_request('GET',
                                     f"{URL_API}/me",
                                     headers=self.headers)
        if response.ok:
            self.api_key = response.json().get("apiKey")
            save_user(self.current_email, self.api_key)
        return response.json()

    def mount_url_login(self):
        html = self.send_request('GET',
                                 f"{BASE_URL}/me",
                                 headers=self.headers).text
        soup = BeautifulSoup(html, 'html.parser')
        auth_client_id = re.findall("AUTH0_CLIENT_ID: '(.*?)',", str(soup))[1]
        authorize_url = (f"https://cnpja.auth0.com/authorize?response_type=token%20id_token&scope=openid%20"
                         f"profile%20email&client_id={auth_client_id}&redirect_uri=https%3A%2F%2Fcnpja.com%2F"
                         f"callback%3FredirectUrl%3Dhttps%253A%252F%252Fcnpja.com%252Fme&nonce=cnpja-website")
        return self.get_url_login(authorize_url)

    def get_url_login(self, url_login):
        return self.send_request('GET',
                                 url_login,
                                 headers=self.headers).url

    def get_data_auth_jwt(self):
        self.headers["origin"] = "https://cnpja.retool.com"
        self.headers["referer"] = "https://cnpja.retool.com/"
        data = {
            "userParams": {
                "queryParams": {
                    "0": re.sub(r"\.|\/|\-|\?", "", self.document),
                    "1": 30,
                    "2": False,
                    "3": "registrations",
                    "4": self.state,
                    "length": 5
                },
                "headersParams": {
                    "0": f"Bearer {self.auth_token}",
                    "length": 1
                },
                "cookiesParams": {
                    "length": 0
                },
                "bodyParams": {
                    "length": 0
                }
            },
            "password": "",
            "environment": "production",
            "queryType": "RESTQuery",
            "frontendVersion": "1",
            "releaseVersion": None,
            "includeQueryExecutionMetadata": True
        }
        self.response = self.send_request('POST',
                                          f"{RETOOL_URL}/public/{URL_ID}/query?queryName=office",
                                          json=data,
                                          headers=self.headers)
        return self.response.json()

    def check_cnpj(self, cnpj):
        self.document = re.sub(r"\.|\/|\-|\?", "", cnpj)
        self.headers["Authorization"] = self.api_key
        self.response = self.send_request('GET',
                                          f"{URL_API}/office/{self.document}?registrations={self.state}",
                                          headers=self.headers)
        return self.response.json()
