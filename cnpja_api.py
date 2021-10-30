import re
import json
import requests
import database
from bs4 import BeautifulSoup

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
        requests.packages.urllib3.disable_warnings()
        self.response = self.session.request(method, url, **kwargs)
        return self.response


class CnpjAPI(Browser):

    def __init__(self, username=None, password=None):
        super().__init__()
        self.username = username
        self.password = password
        self.document = None
        self.state = None
        self.mounted_url_login = None
        self.url_login = None
        self.url_signup = None
        self.auth_token = None
        self.api_key = None

    def signup(self):
        query = {"email": self.username}
        user_data = database.check_existence(query)
        if not user_data["result"]:
            self.mount_url_login()

            self.headers["Referer"] = f"{BASE_URL}/"
            signup_url = self.send_request('GET', self.url_login.replace("login", "signup"), headers=self.headers).url

            self.headers = self.get_headers()
            data = {
                "state": self.url_login.split("=")[1],
                "strengthPolicy": "good",
                "complexityOptions.minLength": 8,
                "email": self.username,
                "password": self.password,
                "action": 'default'
            }
            self.headers["Origin"] = "https://cnpja.auth0.com"
            self.headers["Referer"] = self.url_login.replace("login", "signup")
            self.send_request('POST', signup_url, data=data, headers=self.headers)

            user_profile = self.auth()
            if user_profile.get("status") != "SUSPENDED":
                self.api_key = user_profile.get("apiKey")
                query["key"] = self.api_key
                user_data = database.save(query)
        self.api_key = user_data["object"][0]["api_key"]

    def signup_with_google(self):
        """A url gerada não efetua o login corretamente!!!"""
        self.mount_url_login()

        self.headers["Referer"] = f"{BASE_URL}/"
        self.send_request('GET', self.url_login, headers=self.headers)

        self.headers = self.get_headers()
        data = {
            "state": self.url_login.split("=")[1],
            "connection": 'google-oauth2'
        }
        self.headers["Origin"] = "https://cnpja.auth0.com"
        self.headers["Referer"] = self.url_login
        url_auth_location = self.send_request('POST', self.url_login, data=data, headers=self.headers)

        print(url_auth_location.url)

    def get_token(self):
        data = {
            "username": self.username,
            "password": self.password
        }
        self.auth_token = self.send_request('POST', f"{URL_API}/auth",
                                            json=data, headers=self.headers).json()['idToken']
        return self.auth_token

    def auth(self):
        self.mount_url_login()
        data = {
            "state": self.url_login.split("=")[1],
            "username": self.username,
            "password": self.password,
            "action": "default"
        }
        self.headers["Origin"] = "https://cnpja.auth0.com"
        self.headers["Referer"] = self.url_login
        url_auth = self.send_request('POST', self.url_login, data=data)
        try:
            self.auth_token = re.findall("id_token=(.*?)$", url_auth.url)[0]
        except:
            return {"status": "SUSPENDED"}
        return self.get_user_profile()

    def get_user_profile(self):
        self.headers = self.get_headers()
        self.headers["Origin"] = "https://www.cnpja.com"
        self.headers["referer"] = "https://www.cnpja.com/"
        self.headers["authorization"] = f"Bearer {self.auth_token}"
        return self.send_request('GET', f"{URL_API}/me", headers=self.headers).json()

    def mount_url_login(self):
        html = self.send_request('GET', f"{BASE_URL}/me", headers=self.headers).text
        soup = BeautifulSoup(html, 'html.parser')
        auth_client_id = re.findall("AUTH0_CLIENT_ID: '(.*?)',", str(soup))[1]

        self.mounted_url_login = f"https://cnpja.auth0.com/authorize?response_type=token id_token&scope=openid " \
                                 f"profile email&client_id={auth_client_id}&redirect_uri=https://www.cnpja.com/" \
                                 f"callback?redirectUrl=https://www.cnpja.com/me&nonce=cnpja-website"
        return self.get_url_login()

    def get_url_login(self):
        self.url_login = self.send_request('GET', self.mounted_url_login, headers=self.headers).url
        return self.url_login

    def get_data_auth_jwt(self):
        self.headers["origin"] = "https://cnpja.retool.com"
        self.headers["referer"] = "https://cnpja.retool.com/"
        data = {
            "userParams": {
                "queryParams": {
                    "0": re.sub("\.|\/|\-|\?", "", self.document),
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
        self.response = self.send_request('POST', f"{RETOOL_URL}/public/{URL_ID}/query?queryName=office",
                                          json=data, headers=self.headers)
        return self.response.json()

    def get_data_auth_key(self):
        document = re.sub("\.|\/|\-|\?", "", self.document)
        self.headers["Authorization"] = self.api_key
        data = {
        }
        self.response = self.send_request('GET', f"{URL_API}/office/{document}?registrations={self.state}",
                                          data=data, headers=self.headers)
        return self.response.json()


if __name__ == '__main__':
    cnpj_api = CnpjAPI('user_email', 'user_pass')
    cnpj_api.document = "33.647.553/0001-90"  # "23.041.114/0001-85" "19.495.981/0001-13" "36414225000131"
    cnpj_api.state = "ES"  # SIGLA DO ESTADO ONDE DESEJA CONSULTAR

    # Método cria uma nova conta se a mesma não existir na base de dados local e salva a chave da api para uso posterior
    cnpj_api.signup()  # Cria uma conta e salva a chave da api para consultas posteriores

    # Método de consulta usando autenticação por token jwt
    """
    # cnpj_api.get_token()
    # result = cnpj_api.get_data_auth_jwt()
    # json_data = json.dumps(result["queryData"]["data"], indent=4)
    # print(json_data)
    """

    # Método que utiliza a chave da api através do login, como forma de autenticação
    """
    authentication = cnpj_api.auth()
    profile = cnpj_api.get_user_profile()
    print(json.dumps(profile, indent=4))

    if profile.get("code") == 401:
        print(profile["message"])
    else:
        # print(json.dumps(profile, indent=4))
        cnpj_api.api_key = profile.get("apiKey")
        result = cnpj_api.get_data_auth_key()
        json_data = json.dumps(result, indent=4)
        print(json_data)
    """

    # Método recomendado, utiliza a chave da api diretamente, sem necessidade de login
    result = cnpj_api.get_data_auth_key()
    json_data = json.dumps(result, indent=4)
    print(json_data)
