# -*- coding: utf-8 -*-
import sys
from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand

class PyTest(TestCommand):
    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        import pytest
        errno = pytest.main(self.test_args)
        sys.exit(errno)

with open('README.rst', 'rb') as f:
    long_desc = f.read().decode('utf-8')
        
setup(
    name='nslocalized',
    version='0.1.0',
    description='Reads and writes Mac OS X .strings files',
    long_description=long_desc,
    author='Alastair Houghton',
    author_email='alastair@alastairs-place.net',
    url='http://bitbucket.org/al45tair/nslocalized',
    license='MIT License',
    packages=find_packages(),
    classifiers=[
        'Development Status :: 4 - Beta',
        'License :: OSI Approved :: MIT License',
        'Topic :: Software Development :: Internationalization',
        ],
    tests_require=['pytest'],
    cmdclass={
        'test': PyTest
        },
    install_requires=[
        ],
    provides=['nslocalized']
    )
    
