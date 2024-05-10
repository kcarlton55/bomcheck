'''
setup.py for bomcheck.py.
'''

from setuptools import setup

with open('README.md', 'r') as fh:
    long_description = fh.read()

setup(
    name='bomcheck',   # name people will use to pip install
    python_requires='>=3.8',
    version='1.9.8',
    description='Compare BOMs stored in Excel files.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    license='GPLv3+',
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
    install_requires = ['tomli >= 1.1.0 ; python_version < "3.11"',
                        'pandas>=1.2', 'openpyxl>=3.0', 'requests>=2.29'], # openpyxl needed by pd.read_excel
    url='https://github.com/kcarlton55/bomcheck',
    author='Kenneth Edward Carlton',
    author_email='kencarlton55@gmail.com',
    entry_points={'console_scripts': ['bomcheck=bomcheck:main']},
    keywords='BOM,BOMs,compare,bill,materials,SolidWorks,SyteLine,ERP',
    include_package_data=True,
)
