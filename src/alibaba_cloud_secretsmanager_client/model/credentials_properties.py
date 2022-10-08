# coding=utf-8


class CredentialsProperties:

    def __init__(self,
                 credential=None,
                 secret_name_list=None,
                 region_info_list=None,
                 ignore_ssl_certs=None,
                 dkms_configs_dict=None,
                 private_key_path=None,
                 password=None,
                 source_properties=None):
        self.credential = credential
        self.secret_name_list = secret_name_list
        self.region_info_list = region_info_list
        self.source_properties = source_properties
        self.ignore_ssl_certs = ignore_ssl_certs
        self.dkms_configs_dict = dkms_configs_dict
        self.private_key_path = private_key_path
        self.password = password
