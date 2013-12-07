#!/usr/bin/env python
# encoding: utf-8

from os.path import abspath, dirname, join
from setuptools import setup


here = abspath(dirname(__file__))

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
    'version'              : '0.2.0',
    'description'          : 'tiny hotkey library based on python-evdev',
    'long_description'     : open(join(here, 'README.rst')).read(),
    'author'               : 'Georgi Valkov',
    'author_email'         : 'georgi.t.valkov@gmail.com',
    'license'              : 'Revised BSD License',
    'url'                  : 'https://github.com/gvalkov/pyzmo',
    'keywords'             : 'evdev hotkey',
    'classifiers'          : classifiers,
    'packages'             : ['pyzmo'],
    'package_data'         : {'pyzmo': ['*.hy']},
    'install_requires'     : ['evdev', 'hy'],
    'zip_safe'             : True,
}

if __name__ == '__main__':
    setup(**kw)
