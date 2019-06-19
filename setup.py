from setuptools import setup, find_packages, Extension
import os

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name="Flask-WTFGen",
    version="0.1",
    author = "Ales Hakl",
    author_email = "ales@hakl.net",
    description = ("Flask plugin to automatically generate customizable HTML from wtforms form"),
    long_description=read('README.rst'),
    url="https://github.com/adh/flask-wtfgen",
    
    license="MIT",
    keywords="flask bootstrap wtforms",
    install_requires=[
        'Flask>=1.0',
        'Flask-WTF'
    ],

    packages=[
        "flask_wtfgen",
    ],
    zip_safe=True,
    classifiers=[
        'Development Status :: 3 - Alpha',

        "Framework :: Flask",
        "License :: OSI Approved :: MIT License",

        'Intended Audience :: Developers',

        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],    
)
