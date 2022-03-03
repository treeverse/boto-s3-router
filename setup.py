"""
    Boto S3 Router install script
"""
from setuptools import setup, find_packages
from pathlib import Path
import os

NAME = "boto-s3-router"

this_directory = Path(__file__).parent
LONG_DESCRIPTION = (this_directory / "README.md").read_text()
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
    version=os.getenv('VERSION', '0.0.1'),
    description="Provides a Boto3-like client routing requests to multiple S3 clients",
    long_description=LONG_DESCRIPTION,
    long_description_content_type='text/markdown',
    author="Treeverse",
    author_email="services@treeverse.io",
    url="https://github.com/treeverse/boto-s3-router",
    keywords=["boto", "boto3", "lakeFS", "minio", "AWS", "s3", "router"],
    python_requires=">=3.6",
    install_requires=REQUIRES,
    packages=find_packages(exclude="tests"),
    include_package_data=True,
)

