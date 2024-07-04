import unittest
import sys
import os

# Add the current directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Discover and run tests
loader = unittest.TestLoader()
start_dir = 'tests'
suite = loader.discover(start_dir)

runner = unittest.TextTestRunner()
runner.run(suite)