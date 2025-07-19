from setuptools import setup

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

AUTHOR_NAME = 'PACHI LEE'
SRC_REPO = 'src'
LIST_OF_REQUIREMENTS = ['streamlit',]

setup(
    name = SRC_REPO,
    version='0.01',
    author= AUTHOR_NAME,
    author_email='pachimlee23@gmail.com',
    description= 'movie web app that recommends movies',
    long_description_content_type= 'text/markdown',
    package = [SRC_REPO],
    python_requires = '>=3.7',
    install_reqquires = LIST_OF_REQUIREMENTS,
)
