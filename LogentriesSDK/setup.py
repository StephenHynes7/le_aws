from distutils.core import setup

setup(
    name='LogentriesSDK',
    version='0.1.0',
    author='M. Lacomber',
    author_email='mark@logentries.com',
    packages=['logentriessdk', 'logentriessdk.test'],
    scripts=[],
    data_files=[('logentriessdk', ['logentriessdk/cert.pem'])],
    url='',
    license='LICENSE.txt',
    description='Logentries SDK to programatically manage Logentries accounts.',
    long_description=open('README.txt').read(),
    install_requires=[],
)
