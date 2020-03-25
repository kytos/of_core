"""Setup script.

Run "python3 setup.py --help-commands" to list all available commands and their
descriptions.
"""
import json
import os
import shutil
import sys
from abc import abstractmethod
from pathlib import Path
from subprocess import call, check_call

from setuptools import Command, setup
from setuptools.command.develop import develop
# from setuptools.command.egg_info import egg_info
from setuptools.command.install import install

if 'bdist_wheel' in sys.argv:
    raise RuntimeError("This setup.py does not support wheels")

# Paths setup with virtualenv detection
if 'VIRTUAL_ENV' in os.environ:
    BASE_ENV = Path(os.environ['VIRTUAL_ENV'])
else:
    BASE_ENV = Path('/')

# Kytos var folder
VAR_PATH = BASE_ENV / 'var' / 'lib' / 'kytos'
# Path for enabled NApps
ENABLED_PATH = VAR_PATH / 'napps'
# Path to install NApps
INSTALLED_PATH = VAR_PATH / 'napps' / '.installed'
CURRENT_DIR = Path('.').resolve()

# NApps enabled by default
# CORE_NAPPS = ['of_core']
os.environ["KYTOS_TESTS_SIZE"] = 'small'
os.environ["KYTOS_TESTS_TYPE"] = 'unit'


class SimpleCommand(Command):
    """Make Command implementation simpler."""

    user_options = []

    @abstractmethod
    def run(self):
        """Run when command is invoked.

        Use *call* instead of *check_call* to ignore failures.
        """
    def initialize_options(self):
        """Set default values for options."""

    def finalize_options(self):
        """Post-process options."""


# pylint: disable=attribute-defined-outside-init, abstract-method
class TestCommand(SimpleCommand):
    """Test tags decorators."""

    user_options = [
        ('size=', None, 'Specify the size of tests to be executed.'),
        ('type=', None, 'Specify the type of tests to be executed.'),
    ]

    def initialize_options(self):
        """Set default size and type decorator tests."""
        self.size = 'small'
        self.type = 'unit'

    def finalize_options(self):
        """Post-process."""
        assert self.size in ('small', 'medium', 'large'), 'Invalid size.'
        assert self.type in ('unit', 'integration', 'e2e'), 'Invalid type.'
        os.environ["KYTOS_TESTS_SIZE"] = self.size
        os.environ["KYTOS_TESTS_TYPE"] = self.type


class Cleaner(SimpleCommand):
    """Custom clean command to tidy up the project root."""

    description = 'clean build, dist, pyc and egg from package and docs'

    def run(self):
        """Clean build, dist, pyc and egg from package and docs."""
        call('rm -vrf ./build ./dist ./*.egg-info', shell=True)
        call('find . -name __pycache__ -type d | xargs rm -rf', shell=True)
        call('make -C docs/ clean', shell=True)


class TestCoverage(TestCommand):
    """Display test coverage."""

    description = 'run unit tests and display code coverage'

    def run(self):
        """Run unittest quietly and display coverage report."""
        cmd = 'coverage3 run -m unittest && coverage3 report'
        call(cmd, shell=True)


class Linter(SimpleCommand):
    """Code linters."""

    description = 'lint Python source code'

    def run(self):
        """Run yala."""
        print('Yala is running. It may take several seconds...')
        check_call('yala *.py v0x??/*.py tests/*.py tests/v0x??/*.py',
                   shell=True)


class CITest(TestCommand):
    """Run all CI tests."""

    description = 'run all CI tests: unit and doc tests, linter'

    def run(self):
        """Run unit tests with coverage, doc tests and linter."""
        args = '--size %s --type %s' % (self.size, self.type)
        coverage_cmd = 'python3.6 setup.py coverage %s' % args
        lint_cmd = 'python3.6 setup.py lint'
        cmd = '%s && %s' % (coverage_cmd, lint_cmd)
        check_call(cmd, shell=True)


# class KytosInstall:
#     """Common code for all install types."""
#
#     @staticmethod
#     def enable_core_napps():
#         """Enable a NAPP by creating a symlink."""
#         (ENABLED_PATH / 'kytos').mkdir(parents=True, exist_ok=True)
#         for napp in CORE_NAPPS:
#             napp_path = Path('kytos', napp)
#             src = ENABLED_PATH / napp_path
#             dst = INSTALLED_PATH / napp_path
#             src.symlink_to(dst)


class InstallMode(install):
    """Create files in var/lib/kytos."""

    description = 'To install NApps, use kytos-utils. Devs, see "develop".'

    def run(self):
        """Create of_core as default napps enabled."""
        print(self.description)


# class EggInfo(egg_info):
#     """Prepare files to be packed."""
#
#     def run(self):
#         """Build css."""
#         self._install_deps_wheels()
#         super().run()
#
#     @staticmethod
#     def _install_deps_wheels():
#         """Python wheels are much faster (no compiling)."""
#         print('Installing dependencies...')
#         check_call([sys.executable, '-m', 'pip', 'install', '-r',
#                     'requirements/run.in'])


class DevelopMode(develop):
    """Recommended setup for kytos-napps developers.

    Instead of copying the files to the expected directories, a symlink is
    created on the system aiming the current source code.
    """

    description = 'install NApps in development mode'

    def run(self):
        """Install the package in a developer mode."""
        super().run()
        if self.uninstall:
            shutil.rmtree(str(ENABLED_PATH), ignore_errors=True)
        else:
            self._create_folder_symlinks()
            # self._create_file_symlinks()
            # KytosInstall.enable_core_napps()

    @staticmethod
    def _create_folder_symlinks():
        """Symlink to all Kytos NApps folders.

        ./napps/kytos/napp_name will generate a link in
        var/lib/kytos/napps/.installed/kytos/napp_name.
        """
        links = INSTALLED_PATH / 'kytos'
        links.mkdir(parents=True, exist_ok=True)
        code = CURRENT_DIR
        src = links / 'of_core'
        symlink_if_different(src, code)

        (ENABLED_PATH / 'kytos').mkdir(parents=True, exist_ok=True)
        dst = ENABLED_PATH / Path('kytos', 'of_core')
        symlink_if_different(dst, src)

    # @staticmethod
    # def _create_file_symlinks():
    #     """Symlink to required files."""
    #     src = ENABLED_PATH / '__init__.py'
    #     dst = CURRENT_DIR / 'napps' / '__init__.py'
    #     symlink_if_different(src, dst)


def symlink_if_different(path, target):
    """Force symlink creation if it points anywhere else."""
    # print(f"symlinking {path} to target: {target}...", end=" ")
    if not path.exists():
        # print(f"path doesn't exist. linking...")
        path.symlink_to(target)
    elif not path.samefile(target):
        # print(f"path exists, but is different. removing and linking...")
        # Exists but points to a different file, so let's replace it
        path.unlink()
        path.symlink_to(target)


def read_version_from_json():
    """Read the NApp version from NApp kytos.json file."""
    file = Path('kytos.json')
    metadata = json.loads(file.read_text())
    return metadata['version']


setup(name='kytos_of_core',
      version=read_version_from_json(),
      description='Core NApps developed by Kytos Team',
      url='http://github.com/kytos/of_core',
      author='Kytos Team',
      author_email='of-ng-dev@ncc.unesp.br',
      license='MIT',
      install_requires=['setuptools >= 36.0.1'],
      extras_require={
          'dev': [
              'coverage',
              'pip-tools',
              'yala',
              'tox',
          ],
      },
      cmdclass={
          'clean': Cleaner,
          'ci': CITest,
          'coverage': TestCoverage,

          'develop': DevelopMode,
          'install': InstallMode,
          'lint': Linter,
          # 'egg_info': EggInfo,
      },
      zip_safe=False,
      classifiers=[
          'License :: OSI Approved :: MIT License',
          'Operating System :: POSIX :: Linux',
          'Programming Language :: Python :: 3.6',
          'Topic :: System :: Networking',
      ])
