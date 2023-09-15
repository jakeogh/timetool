# -*- coding: utf-8 -*-


import fastentrypoints
from setuptools import find_packages
from setuptools import setup

dependencies = ["click", "dateparser @ https://github.com/scrapinghub/dateparser"]

config = {
    "version": "0.1",
    "name": "timetool",
    "url": "https://github.com/jakeogh/timetool",
    "license": "ISC",
    "author": "Justin Keogh",
    "author_email": "github.com@v6y.net",
    "description": "Short explination of what it does _here_",
    "long_description": __doc__,
    "packages": find_packages(exclude=["tests"]),
    "package_data": {"timetool": ["py.typed"]},
    "include_package_data": True,
    "zip_safe": False,
    "platforms": "any",
    "install_requires": dependencies,
    "entry_points": {
        "console_scripts": [
            "timetool=timetool.timetool:cli",
        ],
    },
}

setup(**config)
