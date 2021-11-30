"""
    botwo package

"""

from setuptools import setup, find_packages

NAME = "botwo"
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
    description="The botwo package provides a boto3 like client with two underlying boto3 clients",
    author="Treeverse",
    author_email="services@treeverse.io",
    url="https://github.com/treeverse/botwo",
    keywords=["boto", "boto3", "lakeFS"],
    python_requires=">=3.6",
    install_requires=REQUIRES,
    packages=find_packages(exclude="tests"),
    include_package_data=True,
)