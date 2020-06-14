#!/usr/bin/env python

"""
distutils/setuptools install script.
"""
import os
import re

from setuptools import find_packages, setup

ROOT = os.path.dirname(__file__)
VERSION_RE = re.compile(r'__version__ = "([0-9.]+)"')


requires = [
    "botocore>=1.17.2,<1.18.0",
    "jmespath>=0.7.1,<1.0.0",
    "s3transfer>=0.3.0,<0.4.0",
]


def get_version() -> str:
    init = open(os.path.join(ROOT, "boto3", "__init__.py")).read()
    match = VERSION_RE.search(init)
    return match.group(1) if match else "0.0.0"


setup(
    name="boto3-typed",
    version=get_version(),
    description="The AWS SDK for Python",
    long_description=open("README.rst").read(),
    author="Amazon Web Services",
    url="https://github.com/vemel/boto3",
    scripts=[],
    packages=find_packages(exclude=["tests*"]),
    package_data={"boto3": ["data/aws/resources/*.json", "examples/*.rst"]},
    include_package_data=True,
    install_requires=requires,
    license="Apache License 2.0",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Natural Language :: English",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
    ],
)
