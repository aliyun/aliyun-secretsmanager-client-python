# coding=utf-8

from aliyunsdkcore.auth.signers.signer import Signer


class ClientKeySigner(Signer):
    def __init__(self, public_key_id, private_key):
        self._public_key_id = public_key_id
        self._private_key = private_key

    def sign(self, region_id, request):
        header = request.get_signed_header(region_id, self._public_key_id, self._private_key)
        url = request.get_url(region_id, self._public_key_id, self._private_key)
        return header, url
