# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

PKG = 'csvd2c'
SRC = 'src'
EXCLUDES = []
DESC = 'The utility for making dirty to clean of CSV data'
WHO = 'Heo Yongseon'

PKGS = [PKG]
DIRS = {PKG: SRC}
for package in find_packages(SRC, exclude=EXCLUDES):
	PKGS.append('{}.{}'.format(PKG, package))
	DIRS['{}.{}'.format(PKG, package)] = '{}/{}'.format(SRC, package.replace('.', '/'))

setup(
	name=PKG,
	description=DESC,
	long_description=open('README.setup.md', encoding='utf-8').read(),
	long_description_content_type='text/markdown',
	author=WHO,
	url='https://github.com/yong5eon/csvd2c',
	project_urls={
		'Source': 'https://github.com/yong5eon/csvd2c',
		'Issues': 'https://github.com/yong5eon/csvd2c/issues',
		'Releases': 'https://github.com/yong5eon/csvd2c/releases',
	},
	use_scm_version={
		'tag_regex': r'^v?(?P<version>[0-9]+\.[0-9]+\.[0-9]+(?:\.[0-9]+)?(?:(?:rc|\.post)[0-9]+)?)$',
	},
	setup_requires=[
		'setuptools>=77',
		'setuptools-scm>=8,<10',
		'wheel',
	],
	packages=PKGS,
	package_dir=DIRS,
	include_package_data=False,
	package_data={
	},
	classifiers=[
		'Programming Language :: Python :: 3.9',
		'Programming Language :: Python :: 3.10',
		'Programming Language :: Python :: 3.11',
		'Programming Language :: Python :: 3.12',
		'Programming Language :: Python :: 3.13',
		'Programming Language :: Python :: 3.14',
	],
	extras_require={
	},
	python_requires='>=3.9'
)