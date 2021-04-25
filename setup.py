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
                    'aliyun_python_sdk_core>=2.13.30',
                    'aliyun_python_sdk_kms>=2.14.0',
                    'cryptography>=3.2.1',
                    'apscheduler>=3.5.2',
                    'bytebuffer>=0.1.0',
                    'futures; python_version == "2.7"'
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
        "Programming Language :: Python :: Implementation :: CPython",
        "Topic :: Security"
    ],
)
