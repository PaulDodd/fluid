import sys
from setuptools import setup, find_packages

setup(
    name='fluid',
    version='0.0.0',
    packages=find_packages(),
    zip_safe=True,

    author='Paul Dodd',
    author_email='pdodd@umich.edu',
    description="Project to prototype different signac-flow workflows",

    install_requires=['signac', 'signac-flow'],
)
