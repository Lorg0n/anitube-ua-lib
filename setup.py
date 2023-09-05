from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="anitube",
    version="0.1.1",
    author="Lorg0n",
    author_email="lorgon.kv@gmail.com",
    description="Library that parses data from the site anitube.in.ua",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    python_requires='>=3.6',
    install_requires=[
        "requests",
        "beautifulsoup4"
    ]
)