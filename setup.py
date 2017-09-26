"""Setup script.

Run "python3 setup --help-commands" to list all available commands and their
descriptions.
"""
import json
from abc import abstractmethod
from pathlib import Path
from subprocess import call, check_call

from setuptools import Command, setup


def read_version_from_json():
    """Read the NApp version from NApp kytos.json file."""
    file = Path('kytos.json')
    metadata = json.loads(file.read_text())
    return metadata['version']


class SimpleCommand(Command):
    """Make Command implementation simpler."""

    user_options = []

    @abstractmethod
    def run(self):
        """Run when command is invoked.

        Use *call* instead of *check_call* to ignore failures.
        """
        pass

    def initialize_options(self):
        """Set default values for options."""
        pass

    def finalize_options(self):
        """Post-process options."""
        pass


class Cleaner(SimpleCommand):
    """Custom clean command to tidy up the project root."""

    description = 'clean build, dist, pyc and egg from package and docs'

    def run(self):
        """Clean build, dist, pyc and egg from package and docs."""
        call('rm -vrf ./build ./dist ./*.egg-info', shell=True)
        call('find . -name __pycache__ -type d | xargs rm -rf', shell=True)
        call('make -C docs/ clean', shell=True)


class TestCoverage(SimpleCommand):
    """Display test coverage."""

    description = 'run unit tests and display code coverage'

    def run(self):
        """Run unittest quietly and display coverage report."""
        cmd = 'coverage3 run -m unittest discover -qs src' \
              ' && coverage3 report'
        call(cmd, shell=True)


class Linter(SimpleCommand):
    """Code linters."""

    description = 'lint Python source code'

    def run(self):
        """Run pylama."""
        print('Pylama is running. It may take several seconds...')
        check_call('pylama setup.py tests kytos', shell=True)


class CITest(SimpleCommand):
    """Run all CI tests."""

    description = 'run all CI tests: unit and doc tests, linter'

    def run(self):
        """Run unit tests with coverage, doc tests and linter."""
        cmds = ['python setup.py ' + cmd
                for cmd in ('coverage', 'lint')]
        cmd = ' && '.join(cmds)
        check_call(cmd, shell=True)


setup(name='kytos/of_core',
      version=read_version_from_json(),
      description='Core Napps developed by Kytos Team',
      url='http://github.com/kytos/of_core',
      author='Kytos Team',
      author_email='of-ng-dev@ncc.unesp.br',
      license='MIT',
      install_requires=[
          'kytos-utils>=2017.2',
          'kytos>=2017.2',
          'python-openflow>=2017.2'
      ],
      cmdclass={
          'clean': Cleaner,
          'ci': CITest,
          'coverage': TestCoverage,
          'lint': Linter,
      },
      zip_safe=False,
      classifiers=[
          'License :: OSI Approved :: MIT License',
          'Operating System :: POSIX :: Linux',
          'Programming Language :: Python :: 3.6',
          'Topic :: System :: Networking',
      ])
