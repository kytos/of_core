"""Module to test the napp kytos/of_core."""
import sys
import os
from pathlib import Path
​
BASE_ENV = Path(os.environ.get('VIRTUAL_ENV', '/'))
​
NAPPS_DIR = BASE_ENV / 'var/lib/kytos/'
​
sys.path.insert(0, str(NAPPS_DIR))
