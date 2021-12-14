"""
    Boto S3 Router install script
"""
from setuptools import setup, find_packages

NAME = "boto-s3-router"
VERSION = "0.1.0"
# To install the library, run the following
#
# python setup.py install
#
# prerequisite: setuptools
# http://pypi.python.org/pypi/setuptools

REQUIRES = [
    "boto3",
    "fnmatch2",
]

setup(
    name=NAME,
    version=VERSION,
    description="Provides a Boto3-like client routing requests to multiple S3 clients",
    author="Treeverse",
    author_email="services@treeverse.io",
    url="https://github.com/treeverse/botos3router",
    keywords=["boto", "boto3", "lakeFS", "minio"],
    python_requires=">=3.6",
    install_requires=REQUIRES,
    packages=find_packages(exclude="tests"),
    include_package_data=True,
)

