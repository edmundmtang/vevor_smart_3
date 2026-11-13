"""Run both release and legacy engine regression tests."""
import sys
import unittest
from pathlib import Path

root = Path(__file__).resolve().parent
engine = root / "engine"
sys.path.insert(0, str(engine))
sys.path.insert(0, str(root))
loader = unittest.TestLoader()
suite = unittest.TestSuite()
suite.addTests(loader.discover(str(root / "tests")))
suite.addTests(loader.discover(str(engine / "tests")))
result = unittest.TextTestRunner(verbosity=2).run(suite)
sys.exit(0 if result.wasSuccessful() else 1)
