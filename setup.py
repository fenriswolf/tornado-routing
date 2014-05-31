
try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup
    
version = "0.2"

setup(
    name="tornado-routing",
    version=version,
    py_modules=['tornado_routing'],
    author="Fenriswolf",
    description="Flask like routing for tornado server",
    license="http://www.apache.org/licenses/LICENSE-2.0",
    url="https://github.com/fenriswolf/tornado-routing",
    install_requires=['tornado'],
    classifiers=[
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
    ]
)