import pydoitz
import requests
import json
from os import environ
from pydoitz import settings
from pydoitz.cmdb import CMDBNamespace
from pydoitz.idoit import IDoitNamespace
from pydoitz.request import IDoitResponse, IDoitBatchResponse


class IDoitSession():

    def __init__(self, session_id, client_id, user_id):
        self.id = session_id
        self.client_id = client_id
        self.user_id = user_id

    @staticmethod
    def from_resp(resp):
        return IDoitSession(
            session_id=resp.result["session-id"],
            client_id=resp.result["client-id"],
            user_id=resp.result["userid"],
        )


class IDoitClient:

    def __init__(self, host, user=None, password=None, key=None,
                 proto="https", language="en"):
        self.host = host
        self.proto = proto
        self._language = language
        self._session = None
        self._request_id = 0

        # https://kb.i-doit.com/en/i-doit-pro-add-ons/api/index.html#authentication-and-authorization
        self.key = key
        self.user = user
        self.password = password

        self._process_auth_env()
        self._login_file = self._process_auth_file()
        # self._check_auth_data()

        # Bind namespaces
        self.cmdb = CMDBNamespace(self)
        self.idoit = IDoitNamespace(self)

    @property
    def url(self):
        if not self.host:
            raise ValueError("Host cannot be empty or None")
        return f"{self.proto}://{self.host}/i-doit/src/jsonrpc.php"

    @property
    def _headers(self):
        headers = { "Content-Type": "application/json" }
        if self._session:
            headers["X-RPC-Auth-Session"] = self._session.id
        else:
            headers["X-RPC-Auth-Username"] = self.user
            headers["X-RPC-Auth-Password"] = self.password

        return headers

    @property
    def request_cnt(self):
        return self._request_id

    def next_request_id(self):
        self._request_id += 1
        return self.request_cnt

    def _process_auth_file(self):
        login_file = settings.LoginFile()
        if not login_file.entries:
            return None

        entries = login_file.find_entries(self.host, self.user)
        entry = None if not entries else entries[0]

        if entry:
            self.user = entry.user
            self.host = entry.host

            if not self.password:
                self.password = entry.get_credential(entry.password)

            if not self.key:
                self.key = entry.get_credential(entry.key)

        return login_file

    def _process_auth_env(self):
        if not self.user:
            self.user = environ.get("IDOIT_API_USER")

        if not self.password:
            self.password = environ.get("IDOIT_API_PASS")

        if not self.key:
            self.key = environ.get("IDOIT_API_KEY")

        if not self.host:
            self.host = environ.get("IDOIT_API_HOST")

    def _check_auth_data(self):
        if not self.key:
            raise ValueError("An API-Key is required.")

        if self.user:
            if not self.password:
                raise ValueError("Username provided without password.")
        elif self.password:
            raise ValueError("Password provided without Username")

        if not self.host:
            raise ValueError("Host cannot be empty or None")

    def _build_json_single(self, method, params, req_id=None):
        return {
            "method": method,
            "params": {
                "apikey": self.key,
                "language": self._language,
                **params
            },
            "jsonrpc": "2.0",
            "id": self.next_request_id() if not req_id else req_id
        }

    def _build_json_batch(self, reqs):
        data = []
        for req in reqs:
            method = req["method"]
            params = req.get("params", {})
            req_id = req.get("id")
            data.append(self._build_json_single(method, params, req_id))
        return data

    def _run_request(self, data):
        resp = requests.post(
            self.url,
            data=json.dumps(data),
            headers=self._headers
        )
        return resp

    def login(self):
        res = self.request("idoit.login")
        res.check_error()
        self._session = IDoitSession.from_resp(res)

    def logout(self):
        if not self._session:
            return None

        res = self.request("idoit.logout")
        res.check_error()
        self._session = None

    def request(self, method, params={}):
        req = self._build_json_single(method, params)
        resp = self._run_request(req)
        return IDoitResponse(resp.json())

    def batch_request(self, requests):
        req = self._build_json_batch(requests)
        resp = self._run_request(req)
        return IDoitBatchResponse(resp.json())
