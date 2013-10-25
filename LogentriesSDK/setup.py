from distutils.core import setup

setup(
    name='LogentriesSDK',
    version='0.1.0',
    author='M. Lacomber',
    author_email='mark@logentries.com',
    package_dir={'logentriessdk': 'logentriessdk'},
    package_data={'logentriessdk': ['cert.pem']},
    packages=['logentriessdk', 'logentriessdk.test'],
    scripts=[],
    url='',
    license='LICENSE.txt',
    description='Logentries SDK to programatically manage Logentries accounts.',
    long_description=open('README.txt').read(),
    install_requires=[],
)
