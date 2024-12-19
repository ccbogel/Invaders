""" from setup example: https://github.com/pypa/sampleproject/blob/master/setup.py
"""
import sys
from setuptools import setup, find_namespace_packages
from os import path
here = path.abspath(path.dirname(__file__))
# Get the long description from the README file
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()
# Get requirements
with open('requirements.txt') as f:
    required_modules = f.read().splitlines()

mainscript = 'invaders/__main__.py'
OPTIONS = {
    'argv_emulation': True,
    'iconfile': 'invaders/invader.icns'
}

if sys.platform == 'darwin':
     extra_options = dict(
         setup_requires=['py2app'],
         app=[mainscript],
         # Cross-platform applications generally expect sys.argv to
         # be used for opening files.
         options={'py2app': OPTIONS},
     )
elif sys.platform == 'win32':
     extra_options = dict(
         setup_requires=['py2exe'],
         options = {'py2exe': {'bundle_files': 1, 'compressed': True}},
         windows = [{'script': mainscript}],
     )
# older code above the bracket:  app=[mainscript],
else:
     extra_options = dict(
         # Normally unix-like platforms will use "setup.py install"
         # and install the main script as such
         entry_points={
            'console_scripts': ['invaders=invaders.__main__:gui']
         },
     )


setup(
    name='Invaders',
    version='1.0',
    url='http://github.com/ccbogel/Invaders',
    author='Colin Curtain',
    author_email='ccbogel@hotmail.com',
    description='Invaders shoot em up game',
    long_description=long_description,
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Operating System :: OS Independent',
        'Development Status :: 3 - Alpha'
    ],
    keywords='shooting space game',
    packages=find_namespace_packages(include=['invaders','invaders.*']),
    python_requires='>=3.10',
    install_requires=required_modules,
    package_data={
    },
    zip_safe=False,
    include_package_data=True,
    **extra_options
)
