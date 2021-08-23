# coding=utf-8


class CredentialsProperties:

    def __init__(self, credential, secret_name_list, region_info_list, source_properties):
        self.credential = credential
        self.secret_name_list = secret_name_list
        self.region_info_list = region_info_list
        self.source_properties = source_properties
