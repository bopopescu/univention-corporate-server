# -*- coding: utf-8 -*-

#
# Use only Python 2 and 3 compatible code here!
#

#
# Install: pip3 install .
#

import os
import re
import sys
import tempfile
try:
    from urllib import urlretrieve
except ImportError:
    from urllib.request import urlretrieve
import setuptools

changelog_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "debian", "changelog")
chlog_regex = re.compile(r"^(?P<package>.+?) \((?P<version>.+?)\) \w+;")
UCS_RELEASE = "4.4-2"
REPO_RAW_URL = "https://git.knut.univention.de/univention/ucs/raw/{}".format(UCS_RELEASE)
PIP_FALLBACK_URL = "{}/base/univention-config-registry/debian/changelog".format(REPO_RAW_URL)

# when installing using "setup.py install ." the directory is not changed, when using pip, work is done in /tmp
if not os.path.exists(changelog_path):
    _fp, changelog_path = tempfile.mkstemp()
    urlretrieve(PIP_FALLBACK_URL, changelog_path)

with open(changelog_path) as fp:
    for line in fp:
        m = chlog_regex.match(line)
        if m:
            break
    else:
        print("Could not parse find package name and version in {}.".format(changelog_path))
        sys.exit(1)

setuptools.setup(
    name=m.groupdict()["package"],
    version=m.groupdict()["version"],
    author="Univention GmbH",
    author_email="packages@univention.de",
    description="Python interface to configuration registry",
    long_description="Python interface to configuration registry",
    url="https://www.univention.de/",
    install_requires=["six"],
    packages=["univention", "univention.config_registry"],
    scripts=["univention-config-registry"],
    license="GNU Affero General Public License v3",
    classifiers=[
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU Affero General Public License v3",
        "Operating System :: OS Independent",
    ],
)
