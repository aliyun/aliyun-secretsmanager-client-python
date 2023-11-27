# coding=utf-8
# !/usr/bin/python

"""Alibaba Cloud Secrets Manager Client for Python."""
import os
import re

from setuptools import find_packages, setup

VERSION_RE = re.compile(r"""__version__ = ['"]([0-9.]+)['"]""")
HERE = os.path.abspath(os.path.dirname(__file__))


def read(*args):
    """Reads complete file contents."""
    return open(os.path.join(HERE, *args), 'rb').read().decode(encoding="utf-8")


def get_version():
    """Reads the version from this module."""
    init = read("src", "alibaba_cloud_secretsmanager_client", "__init__.py")
    return VERSION_RE.search(init).group(1)


setup(
    name="aliyun-secret-manager-client",
    packages=find_packages("src"),
    package_dir={"": "src"},
    version=get_version(),
    license="Apache License 2.0",
    author="Alibaba Cloud",
    maintainer="Alibaba Cloud",
    description="Alibaba Cloud Secrets Manager Client implementation for Python",
    long_description=read("README.rst"),
    keywords=["aliyun", "kms", "secrets-manager"],
    install_requires=[
        "aliyun_python_sdk_core>=2.13.30",
        "aliyun_python_sdk_kms>=2.14.0",
        "alibabacloud-dkms-gcs==1.0.2; python_version>='3'",
        "alibabacloud-dkms-gcs-python2==1.0.4; python_version<'3'",
        "alibabacloud-dkms-transfer-python==0.1.2; python_version>'3'",
        "alibabacloud-dkms-transfer-python2==0.1.3; python_version<'3'",
        "cryptography>=3.2.1",
        "apscheduler>=3.5.2",
        "bytebuffer>=0.1.0",
        "pyopenssl>=16.2.0",
        "futures; python_version=='2.7'",
        "cryptography<=3.3.2; python_version=='2.7'",
        "cryptography<=38.0.3; python_version>='3'",
        "pyopenssl<=21.0.0; python_version=='2.7'",
        "multidict<=5.1.0; python_version>='3'",
        "apscheduler<=3.8.0",
        "protobuf<=3.17.0; python_version<='3.6'",
        "protobuf<=3.20.2; python_version>='3.7'",
        "typing_extensions<= 3.10.0.2; python_version=='2.7'",
        "typing_extensions<= 4.1.1; python_version>='3'",
    ],
    include_package_data=True,
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: Implementation :: CPython",
        "Topic :: Security"
    ],
)
