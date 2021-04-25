Aliyun Secrets Manager Client for Python
========================================

The Aliyun Secrets Manager Client for Python enables Python developers
to easily work with Aliyun KMS Secrets.

Read this in other languages: 简体中文
<https://github.com/aliyun/aliyun-secretsmanager-client-python/blob/master/README.zh-cn.rst>

-  `Aliyun Secrets Manager Client
   Homepage <https://help.aliyun.com/document_detail/190269.html?spm=a2c4g.11186623.6.621.201623668WpoMj>`__
-  `Issues <https://github.com/aliyun/aliyun-secretsmanager-client-python/issues>`__
-  `Release <https://github.com/aliyun/aliyun-secretsmanager-client-python/releases>`__

License
-------

`Apache License
2.0 <https://www.apache.org/licenses/LICENSE-2.0.html>`__

Features
--------

-  Provide quick integration capability to gain secret information
-  Provide Alibaba secrets cache ( memory cache or encryption file cache
   )
-  Provide tolerated disaster by the secrets with the same secret name
   and secret data in different regions
-  Provide default backoff strategy and user-defined backoff strategy

Requirements
------------

Python 2.7，3.5，3.6，3.7

Install
-------

Install the official release version through PIP (taking Linux as an
example):

.. code:: bash

   $ pip install aliyun-secret-manager-client

You can also install the unzipped installer package directly:

.. code:: bash

   $ sudo python setup.py install

Sample Code
-----------

Ordinary User Sample Code
~~~~~~~~~~~~~~~~~~~~~~~~~

-  Build Secrets Manager Client by system environment variables (`system
   environment variables setting for details <README_environment.md>`__)

.. code:: python

   from alibaba_cloud_secretsmanager_client.secret_manager_cache_client_builder import SecretManagerCacheClientBuilder

   if __name__ == '__main__':
       secret_cache_client = SecretManagerCacheClientBuilder.new_client()
       secret_info = secret_cache_client.get_secret_info("#secretName#")
       print(secret_info.__dict__)

-  Build Secrets Manager Client by the given parameters(accessKey,
   accessSecret, regionId, etc)

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

Particular User Sample Code
~~~~~~~~~~~~~~~~~~~~~~~~~~~

-  Use custom parameters or customized implementation

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
