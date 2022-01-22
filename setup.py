
'''
Intial structure before creating a package:

bomcheck/
    src/
        __init__.py
        bomcheck.py
    LICENSE.txt
    README.md
    setup.py

Where __init__.py is a text file that is empty.
'''

from setuptools import setup

with open('README.md', 'r') as fh:
    long_description = fh.read()

setup(
    name='bomcheck',   # name people will use to pip install
    version='1.8.1',
    description='Compare BOMs stored in Excel files.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    py_modules=['bomcheck'],
    package_dir={'': 'src'},
    classifiers=[
        'Programming Language :: Python :: 3',
        'Development Status :: 5 - Production/Stable',
        'Natural Language :: English',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Intended Audience :: Manufacturing',
        'Intended Audience :: End Users/Desktop',
        'Operating System :: OS Independent',],
    install_requires = ['pandas>=1.2', 'openpyxl>=3.0', 'xlrd>=1.2.0', 'xlsxwriter>=1.1'],
    url='https://github.com/kcarlton55/bomcheck',
    author='Kenneth Edward Carlton',
    author_email='kencarlton55@gmail.com',
    entry_points={'console_scripts': ['bomcheck=bomcheck:main']},
    keywords='BOM,BOMs,compare,bill,materials',
)