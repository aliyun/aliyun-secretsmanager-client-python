import unittest

from alibaba_cloud_secretsmanager_client.model.region_info import RegionInfo
from alibaba_cloud_secretsmanager_client.service.default_secret_manager_client_builder import sort_region_info_list


class TestSortRegionInfoList(unittest.TestCase):

    def test_sort_region_info_list(self):
        region_info_list = []
        region_info1 = RegionInfo("cn-hangzhou")
        region_info2 = RegionInfo("cn-shanghai", True)
        region_info3 = RegionInfo("cn-beijing")
        region_info4 = RegionInfo("cn-shenzhen")
        region_info_list.append(region_info4)
        region_info_list.append(region_info3)
        region_info_list.append(region_info2)
        region_info_list.append(region_info1)
        sorted_list = sort_region_info_list(region_info_list)
        print(sorted_list)
