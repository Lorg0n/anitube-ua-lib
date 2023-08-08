from setuptools import setup, find_packages

setup(
    name="anitube-ua-lib",
    version="0.1",
    author='Lorg0n',
    url='https://github.com/Lorg0n/anitube-ua-lib',
    description='Library that parses data from the site anitube.in.ua',
    install_requires=['beautifulsoup4', 'requests-cache'],
    packages=find_packages(),
)