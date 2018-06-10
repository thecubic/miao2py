#!/usr/bin/env python3

from setuptools import setup, find_packages

setup(
    name='miaomiaopy',
    version='0.0.1',
    description='interact with MiaoMiao devices in Python3',
    url='https://github.com/thecubic/miaomiaopy',
    author='Dave Carlson',
    author_email='thecubic@thecubic.net',
    license='Apache 2.0',
    classifiers=[
        # 'Development Status :: 5 - Production/Stable',
        # 'Intended Audience :: End Users/Desktop',
        # 'Topic :: Multimedia :: Video',
        # 'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
    scripts=[
        'scripts/mmr-decode',
        'scripts/mmr-mqp',
        'scripts/mmr-mqs',
    ],
    packages=find_packages(),
    install_requires=[
        'bluepy',
    ]
)
