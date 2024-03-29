# -*- coding: utf-8 -*-


from setuptools import find_packages
from setuptools import setup

import fastentrypoints

dependencies = [
    "click",
    "pytz",
    "dateparser @ git+https://github.com/scrapinghub/dateparser",
    "humanize @ git+https://github.com/jmoiron/humanize",
    "asserttool @ git+https://git@github.com/jakeogh/asserttool",
    "clicktool @ git+https://git@github.com/jakeogh/clicktool",
]

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
