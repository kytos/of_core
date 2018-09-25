"""Module to test the napp kytos/of_core."""
import sys
import os
from pathlib import Path

if 'VIRTUAL_ENV' in os.environ:
    BASE_ENV = Path(os.environ['VIRTUAL_ENV'])
else:
    BASE_ENV = Path('/')

OF_CORE_PATH = BASE_ENV / '/var/lib/kytos/napps/..'

sys.path.insert(0, str(OF_CORE_PATH))
