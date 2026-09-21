import os
import sys

# Make `from core import ...` work in tests by putting odin_qa/ on the import path
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "odin_qa"))
