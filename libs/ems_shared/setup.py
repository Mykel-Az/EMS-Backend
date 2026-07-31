# libs/ems_shared/setup.py
from setuptools import setup, find_packages

setup(
    name="ems_shared",
    version="0.1.0",
    packages=find_packages(),
    install_requires=["PyJWT>=2.8.0"],
)