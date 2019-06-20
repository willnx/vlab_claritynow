#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
claritynow RESTful API
"""
from setuptools import setup, find_packages


setup(name="vlab-claritynow-api",
      author="Nicholas Willhite,",
      author_email='willnx84@gmail.com',
      version='2019.6.20',
      packages=find_packages(),
      include_package_data=True,
      package_files={'vlab_claritynow_api' : ['app.ini']},
      description="claritynow",
      install_requires=['flask', 'ldap3', 'pyjwt', 'uwsgi', 'vlab-api-common',
                        'ujson', 'cryptography', 'vlab-inf-common', 'celery']
      )
