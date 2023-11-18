'''
setup.py for bomcheck.py.
'''

from setuptools import setup

with open('README.md', 'r') as fh:
    long_description = fh.read()

setup(
    name='bomcheck',   # name people will use to pip install
    python_requires='>=3.11',
    version='1.9.5',
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
    install_requires = ['pandas>=1.2', 'toml>=0.10', 'openpyxl>=3.0'], # openpyxl needed for pd.read_excel
    url='https://github.com/kcarlton55/bomcheck',
    author='Kenneth Edward Carlton',
    author_email='kencarlton55@gmail.com',
    entry_points={'console_scripts': ['bomcheck=bomcheck:main']},
    keywords='BOM,BOMs,compare,bill,materials,SolidWorks,SyteLine,ERP',
)
