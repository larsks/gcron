from setuptools import setup, find_packages

setup(name='netreg',
        version='0.1',
        description='automate your computer using Google Calendar',
        author='Lars Kellogg-Stedman',
        author_email='lars@oddbit.com',
        packages=['gcron'],
        install_requires=['vobject', 'python-dateutil', 'pytz'],
        )
