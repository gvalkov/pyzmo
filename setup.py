#!/usr/bin/env python
# encoding: utf-8

from os.path import abspath, dirname, join
from setuptools import setup


here = abspath(dirname(__file__))
requires = ('evdev',)
#test_requires = ('pytest',)

classifiers = (
    'Development Status :: 3 - Alpha',
    'Programming Language :: Python :: 2.7',
    'Programming Language :: Python :: 3',
    'Programming Language :: Python :: 3.1',
    'Programming Language :: Python :: 3.2',
    'Programming Language :: Python :: 3.3',
    'License :: OSI Approved :: BSD License',
    'Intended Audience :: Developers',
    'Operating System :: POSIX :: Linux',
)

kw = {
    'name'                 : 'pyzmo',
    'version'              : '0.1.0',

    'description'          : 'tiny hotkey library based on python-evdev',
    'long_description'     : open(join(here, 'README.rst')).read(),

    'author'               : 'Georgi Valkov',
    'author_email'         : 'georgi.t.valkov@gmail.com',
    'license'              : 'New BSD License',
    'url'                  : 'https://github.com/gvalkov/pyzmo',

    'keywords'             : 'evdev hotkey',
    'classifiers'          : classifiers,

    'packages'             : ['pyzmo'],
    'install_requires'     : requires,
    'zip_safe'             : True,
}

setup(**kw)
