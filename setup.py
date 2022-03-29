#!/usr/bin/env python

from distutils.core import setup

setup(name='reccor',
      version='0.0.2',
      description='Python (Rec)cord (Cor)relator',
      author='shn-shp',
      url='https://github.com/shn-shp/reccor',
      install_requires=[
            "PyYAML",
            "watchdog"
      ],
      license="BSD-3-Clause",
      entry_points={
            'console_scripts': ['reccor=reccor.cli:main'],
      },
      packages=['reccor', 'reccor.modules'],
      classifiers=[
            "Development Status :: 3 - Alpha",
            "License :: OSI Approved :: BSD License",
            "Operating System :: POSIX :: Linux",
            "Programming Language :: Python :: 3",
            "Topic :: Scientific/Engineering :: Information Analysis"
      ]
      )
