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


from alibaba_cloud_secretsmanager_client.utils import secret_const


class SecretInfo:

    def __init__(self, secret_name=None, version_id=None, secret_value=None, secret_data_type=None, create_time=None,
                 secret_type=None, automatic_rotation=None, extended_config=None, rotation_interval=None,
                 next_rotation_date=None,
                 secret_value_byte_buffer=None):
        """"""
        self.secret_name = secret_name
        self.version_id = version_id
        self.secret_value = secret_value
        self.secret_data_type = secret_data_type
        self.create_time = create_time
        self.secret_type = secret_type
        self.automatic_rotation = automatic_rotation
        self.extended_config = extended_config
        self.rotation_interval = rotation_interval
        self.next_rotation_date = next_rotation_date
        self.secret_value_byte_buffer = secret_value_byte_buffer

    def __repr__(self):
        return repr((self.secret_name, self.version_id,
                     self.secret_value,
                     self.secret_data_type, self.create_time,
                     self.secret_type, self.automatic_rotation, self.extended_config, self.rotation_interval,
                     self.next_rotation_date, self.secret_value_byte_buffer))


class CacheSecretInfo:

    def __init__(self, stage='ACSCurrent', refresh_time_stamp=0, secret_info=None):
        """"""
        self.secret_info = secret_info
        self.stage = stage
        self.refresh_time_stamp = refresh_time_stamp


def convert_json_to_secret_info(json):
    return SecretInfo(json.get(secret_const.SECRET_KEY_NAME_SECRET_NAME),
                      json.get(secret_const.SECRET_KEY_NAME_VERSION_ID),
                      json.get(secret_const.SECRET_KEY_NAME_SECRET_DATA),
                      json.get(secret_const.SECRET_KEY_NAME_SECRET_DATA_TYPE),
                      json.get(secret_const.SECRET_KEY_NAME_CREATE_TIME),
                      json.get(secret_const.SECRET_KEY_NAME_SECRET_TYPE),
                      json.get(secret_const.SECRET_KEY_NAME_AUTOMATIC_ROTATION),
                      json.get(secret_const.SECRET_KEY_NAME_EXTENDED_CONFIG),
                      json.get(secret_const.SECRET_KEY_NAME_ROTATION_INTERVAL),
                      json.get(secret_const.SECRET_KEY_NAME_NEXT_ROTATION_DATE))


def convert_dict_to_cache_secret_info(cache_secret_info_dict):
    cache_secret_info = CacheSecretInfo()
    secret_info = SecretInfo()
    cache_secret_info_keys = cache_secret_info.__dict__.keys()
    secret_info_key_name = "secret_info"
    for cache_secret_info_key in cache_secret_info_keys:
        value = cache_secret_info_dict.get(cache_secret_info_key)
        if value is not None and not isinstance(value, dict):
            setattr(cache_secret_info, cache_secret_info_key, value)
        if cache_secret_info_key is secret_info_key_name:
            secret_info_dic = cache_secret_info_dict.get(secret_info_key_name)
            for secret_info_key in secret_info.__dict__.keys():
                value = secret_info_dic.get(secret_info_key)
                if value is not None:
                    setattr(secret_info, secret_info_key, value)
    cache_secret_info.secret_info = secret_info
    return cache_secret_info

