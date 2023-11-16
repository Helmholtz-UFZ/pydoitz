class IDoitError(Exception):

    def __init__(self, rc, msg):
        self.msg = msg
        self.rc = rc
        super().__init__(f"{self.rc}: {self.msg}")

    @staticmethod
    def from_resp(resp):
        if "error" in resp:
            data = resp["error"]
            message = data["message"]
            code = data["code"]

            # Check if we can find a specific Error
            for err in IDOIT_API_ERRORS:
                if err.ERROR_CODE == code:
                    return err(rc=code, msg=message)

            # Otherwise just return a generic Error
            return IDoitError(rc=code, msg=message)
        else:
            return None


class InvalidParamsError(IDoitError):
    ERROR_CODE = -32602


class ParseError(IDoitError):
    ERROR_CODE = -32700


class InvalidRequestError(IDoitError):
    ERROR_CODE = -32600


class MethodNotFoundError(IDoitError):
    ERROR_CODE = -32601


class InternalError(IDoitError):
    ERROR_CODE = -32603


class SystemError(IDoitError):
    ERROR_CODE = -32099


IDOIT_API_ERRORS = [
    InvalidParamsError,
    ParseError,
    InvalidRequestError,
    MethodNotFoundError,
    InternalError,
    SystemError
]
