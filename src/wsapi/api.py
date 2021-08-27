import time
import requests
import urllib.parse
import hashlib
import hmac
import base64


def get_nonce():
    """
    kraken rest api requires a nonce that needs to be incremented for
    each request.
    """
    return int(time.time() * 1000)


class API:
    """ Kraken REST API """

    def __init__(self, api_key: str = None, api_secret: str = None):
        self.api_key = api_key
        self.api_secret = api_secret
        self.uri = "https://api.kraken.com"
        self.api_version = "0"

    def __sign(self, data: dict, url_path: str):
        assert self.api_key is not None and self.api_secret is not None

        post_data = urllib.parse.urlencode(data)
        encoded = (str(data["nonce"]) + post_data).encode()
        message = url_path.encode() + hashlib.sha256(encoded).digest()

        secret64 = base64.b64decode(self.api_secret)
        signature = hmac.new(secret64, message, hashlib.sha512)
        sig_digest = base64.b64encode(signature.digest())

        return sig_digest.decode()

    def __query(self, url_path: str, data: dict, headers=None, timeout=None):
        data = data or {}
        headers = headers or {}

        url = self.uri + url_path
        res = requests.post(url, data=data, headers=headers, timeout=timeout)

        if not res.ok:
            res.raise_for_status()

        return res.json()

    def query_public(self, method: str, data: dict = None, timeout: int = 5):
        """ public api call """
        data = data or {}
        url_path = f"/{self.api_version}/public/{method}"
        return self.__query(url_path, data, timeout=timeout)

    def query_private(self, method: str, data: dict = None, timeout: int = 5):
        """ private api call """

        data = data or {}
        data["nonce"] = get_nonce()

        url_path = f"/{self.api_version}/private/{method}"

        sign = self.__sign(data, url_path)
        headers = {"API-Key": self.api_key, "API-Sign": sign}
        return self.__query(url_path, data, headers, timeout)
