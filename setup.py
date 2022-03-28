
"""
Metabet python package configuration.
"""
from setuptools import setup
setup(
    name='metabet',
    version='0.1.0',
    packages=['metabet'],
    include_package_data=True,
    install_requires=[
        'arrow',
        'bs4',
        'Flask',
        'html5validator',
        'pycodestyle',
        'pydocstyle',
        'pylint',
        'pytest',
        'pytest-mock',
        'requests',
    ],
    python_requires='>=3.6',
)