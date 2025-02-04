#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re

from setuptools import setup, find_packages

################################
# Required developer input start
################################

# Python versions this package is compatible with
python_requires = '>=3.6, <4'

# Packages that this package imports. List everything apart from standard lib packages.
install_requires = [
    'sensirion-i2c-driver',
    'sensirion-shdlc-driver',
    'sensirion-shdlc-sensorbridge'
]

# Packages required for tests and docs
extras_require = {
    'test': [
        'flake8~=6.0.0',
        'pytest~=8.1.1',
        'pytest-cov~=5.0.0',
    ],
    'docs': [
        'lazy-object-proxy ~=1.7.1',
        'sphinx~=7.1.0',
        'docutils~=0.18.0',
        'sphinx_rtd_theme~=1.3.0',
        'sphinx-autoapi~=3.0.0'
    ]
}

package_name = "sensirion-driver-adapters"
author = 'Rolf Laich'
author_email = 'rolf.laich@sensirion.com'
description = 'Adapter classes to use sensirion_i2c_driver package'
keywords = 'driver driver-generator'

################################
# Required developer input end
################################

assert (package_name != "<sensirion-package-name>")
assert (author != "<full name author>")
assert (author_email != '<firstname.familyname>@sensirion.com')
assert (description != '<short description of the package>')
assert (keywords != '<keywords meaningful>')

# Note: Remove this check only for old packages which do not (yet) have the
# "sensirion-" prefix for compatibility reasons.
assert (package_name.startswith("sensirion-"))

# It is important to NOT import anything, not even the version, from the package which is being built.
# Otherwise weird behavior is guaranteed.
version_line = open(os.path.join(package_name.replace("-", "_"), "version.py"), "rt").read()
result = re.search(r"^version = ['\"]([^'\"]*)['\"]", version_line, re.M)
if result:
    version_string = result.group(1)
else:
    raise RuntimeError("Unable to find version string")

long_description = open(os.path.join(os.path.dirname(__file__), 'README.rst')).read().strip() + "\n\n" + \
                   open(os.path.join(os.path.dirname(__file__), 'CHANGELOG.rst')).read().strip() + "\n"
setup(
    name=package_name,
    version=version_string,
    author=author,
    author_email=author_email,
    description=description,
    license='BSD 3-Clause License',
    keywords=keywords,
    url='http://developers.sensirion.com',
    packages=find_packages(exclude=['tests', 'tests.*']),
    long_description=long_description,
    python_requires=python_requires,
    install_requires=install_requires,
    extras_require=extras_require,
    classifiers=[
        'Intended Audience :: Developers',
        'License :: Other/Proprietary License',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.11',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ]
)
