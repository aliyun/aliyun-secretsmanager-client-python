阿里云凭据管家Python客户端
==========================

阿里云凭据管家Python客户端可以使Python开发者快速使用阿里云凭据。

其他语言版本: English
<https://github.com/aliyun/aliyun-secretsmanager-client-python/blob/master/README.rst>

-  `阿里云凭据管家客户端主页 <https://help.aliyun.com/document_detail/190269.html?spm=a2c4g.11186623.6.621.201623668WpoMj>`__
-  `Issues <https://github.com/aliyun/aliyun-secretsmanager-client-python/issues>`__
-  `Release <https://github.com/aliyun/aliyun-secretsmanager-client-python/releases>`__

许可证
------

`Apache License
2.0 <https://www.apache.org/licenses/LICENSE-2.0.html>`__

优势
----

-  支持用户快速集成获取凭据信息
-  支持阿里云凭据管家内存和文件两种缓存凭据机制
-  支持凭据名称相同场景下的跨地域容灾
-  支持默认规避策略和用户自定义规避策略

软件要求
--------

Python 2.7，3.4，3.5，3.6，3.7

安装
----

通过pip安装官方发布的版本（以Linux系统为例）：

.. code:: bash

   $ pip install aliyun-secret-manager-client

也可以直接安装解压后的安装包：

.. code:: bash

   $ sudo python setup.py install

示例代码
--------

一般用户代码
~~~~~~~~~~~~

-  通过系统环境变量或配置文件(secretsmanager.properties)构建客户端(`系统环境变量设置详情 <README_environment.zh-cn.md>`__\ 、\ `配置文件设置详情 <README_config.zh-cn.md>`__)

.. code:: python

   from alibaba_cloud_secretsmanager_client.secret_manager_cache_client_builder import SecretManagerCacheClientBuilder

   if __name__ == '__main__':
       secret_cache_client = SecretManagerCacheClientBuilder.new_client()
       secret_info = secret_cache_client.get_secret_info("#secretName#")
       print(secret_info.__dict__)

-  通过指定参数(accessKey、accessSecret、regionId等)构建客户端

.. code:: python

   from alibaba_cloud_secretsmanager_client.secret_manager_cache_client_builder import SecretManagerCacheClientBuilder
   from alibaba_cloud_secretsmanager_client.service.default_secret_manager_client_builder import DefaultSecretManagerClientBuilder

   if __name__ == '__main__':
       secret_cache_client = SecretManagerCacheClientBuilder.new_cache_client_builder(DefaultSecretManagerClientBuilder.standard() \
           .with_access_key("#accessKeyId#", "#accessKeySecret#") \
           .with_region("#regionId#").build()) \
       .build();
       secret_info = secret_cache_client.get_secret_info("#secretName#")
       print(secret_info.__dict__)

定制化用户代码
~~~~~~~~~~~~~~

-  使用自定义参数或用户自己实现

.. code:: python

   from alibaba_cloud_secretsmanager_client.secret_manager_cache_client_builder import SecretManagerCacheClientBuilder
   from alibaba_cloud_secretsmanager_client.cache.file_cache_secret_store_strategy import FileCacheSecretStoreStrategy
   from alibaba_cloud_secretsmanager_client.service.default_secret_manager_client_builder import DefaultSecretManagerClientBuilder
   from alibaba_cloud_secretsmanager_client.service.default_refresh_secret_strategy import DefaultRefreshSecretStrategy
   from alibaba_cloud_secretsmanager_client.service.full_jitter_back_off_strategy import FullJitterBackoffStrategy

   if __name__ == '__main__':
       secret_cache_client = SecretManagerCacheClientBuilder \
       .new_cache_client_builder(DefaultSecretManagerClientBuilder.standard().with_access_key("#accessKeyId#", "#accessKeySecret#") \
            .with_back_off_strategy(FullJitterBackoffStrategy(3, 2000, 10000)) \
            .with_region("#regionId#").build()) \
        .with_cache_secret_strategy(FileCacheSecretStoreStrategy("#cacheSecretPath#", True,"#salt#")) \
        .with_refresh_secret_strategy(DefaultRefreshSecretStrategy("#ttlName#")) \
        .with_cache_stage("#stage#") \
        .with_secret_ttl("#secretName#", 1 * 60 * 1000l) \
        .build()
       secret_info = secret_cache_client.get_secret_info("#secretName#")
       print(secret_info.__dict__)
