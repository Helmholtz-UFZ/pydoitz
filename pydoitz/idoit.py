import pydoitz
from pydoitz.request import IDoitRequest


class IDoitNamespace(IDoitRequest):

    def version(self):
        resp = self._client.request(method="idoit.version")
        resp.check_error()
        return resp.result

    def constants(self):
        resp = self._client.request(method="idoit.constants")
        resp.check_error()
        return resp.result

    def search(self):
        pass
