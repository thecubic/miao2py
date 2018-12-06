#!/usr/bin/env python3

from setuptools import setup, find_packages

setup(
    name="miao2py",
    version="0.0.6",
    description="interact with MiaoMiao devices in Python3",
    url="https://github.com/thecubic/miao2py",
    author="Dave Carlson",
    author_email="thecubic@thecubic.net",
    license="Apache 2.0",
    classifiers=[
        # 'Development Status :: 5 - Production/Stable',
        # 'Intended Audience :: End Users/Desktop',
        # 'Topic :: Multimedia :: Video',
        # 'License :: OSI Approved :: MIT License',
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
    ],
    scripts=[
        "scripts/m2p-decode",
        "scripts/m2p-mqp",
        "scripts/m2p-mqs",
        "scripts/m2p-scan",
    ],
    packages=find_packages(),
    install_requires=["bluepy", "hbmqtt", "click"],
)
