# coding=utf-8
# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
#
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License

import hashlib

from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

secret_key = lambda key, salt: hashlib.pbkdf2_hmac('sha256', key, salt, 65536)


class AESEncoder:

    def __init__(self, key, iv, salt, data):
        self.key = key
        self.iv = iv
        self.salt = salt
        self.data = data

    def encode(self):
        padder = padding.PKCS7(algorithms.AES.block_size).padder()
        padder_data = padder.update(self.data.encode('utf-8'))
        padder_data += padder.finalize()
        cipher = Cipher(algorithms.AES(secret_key(self.key, self.salt)), modes.CBC(self.iv))
        encryptor = cipher.encryptor()
        return encryptor.update(padder_data) + encryptor.finalize()


class AESDecoder:

    def __init__(self, key, iv, salt, data):
        self.key = key
        self.iv = iv
        self.salt = salt
        self.data = data

    def decode(self):
        cipher = Cipher(algorithms.AES(secret_key(self.key, self.salt)), modes.CBC(self.iv))
        unpadder = padding.PKCS7(algorithms.AES.block_size).unpadder()
        decryptor = cipher.decryptor()
        decryptor_data = decryptor.update(self.data) + decryptor.finalize()
        return unpadder.update(decryptor_data) + unpadder.finalize()
