from __future__ import print_function  
from setuptools import setup, find_packages  
import sys  
  
setup(  
    name="fxpath",
    version="0.1.3",
    author="vilame",
    author_email="opaquism@hotmail.com",
    description="search same xpath and inner diff on 2 or more than 2 htmlcontent.",
    long_description="import fxpath; help(fxpath)",
    license="MIT",
    url="https://pypi.org/project/fxpath/",
    packages=['fxpath'],
    classifiers=[
        "Environment :: Web Environment",
        "Intended Audience :: Developers",
        "Operating System :: OS Independent",
    ]
)  
