import json
from pydoitz.exceptions import IDoitError


class IDoitResponse():

    def __init__(self, resp):
        self.json = resp
        self.error = IDoitError.from_resp(resp)
        self.result = []
        self.version = None
        self.request_id = None

        if isinstance(resp, dict):
            self.result = resp.get("result", None)
            self.version = resp["jsonrpc"]
            self.request_id = resp["id"]

    def check_error(self):
        if self.error:
            raise self.error
        else:
            return self

    def dump(self):
        if self.error:
            print(self.error.msg, self.error.rc)
        else:
            print(json.dumps(self.result, indent=4))


class IDoitBatchResponse(list):

    def __init__(self, resp):
        super().__init__()

        if isinstance(resp, dict):
            self.append(IDoitResponse(resp))
        else:
            for res in resp:
                self.append(IDoitResponse(res))

    def results(self):
        for item in self:
            yield item.result

    def check_error(self):
        for item in self:
            item.check_error()
        return self

    def dump(self):
        for item in self:
            item.dump()


class IDoitRequest:

    def __init__(self, client):
        self._client = client
