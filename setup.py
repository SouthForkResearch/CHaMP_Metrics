# -*- coding: utf-8 -*-

"""setup.py: setuptools control."""
"""
A Lot of this methodology was "borrowed" from
    - https://github.com/jgehrcke/python-cmdline-bootstrap/blob/master/bootstrap/bootstrap.py
"""

import re
from setuptools import setup

install_requires = [
    'argparse', 'shapely', 'numpy'
]

version = re.search(
      '^__version__\s*=\s*"(.*)"',
      open('__version__.py').read(),
      re.M
).group(1)

with open("README.md", "rb") as f:
      long_descr = f.read().decode("utf-8")

setup(
      name='CHaMPToolbox',
      description='Tools that are part of the CHaMP Automation pipeline',
      url='https://github.com/SouthForkResearch/CHaMPToolbox',
      author='Matt Reimer',
      author_email='matt@northarrowresearch.com',
      license='MIT',
      packages=['tools'],
      zip_safe=False,
      install_requires=install_requires,
      entry_points={
            "console_scripts": [
                  'champtopometrics = tools.topometrics.topometrics:main',
                  'champvalidation = tools.validation.validation:main',
                  'champhydroprep = tools.hydroprep:main',
                  'champsiteprops = tools.siteprops:main',
            ]
      },
      version=version,
      long_description=long_descr,
)
