# coding: utf-8
# flake8: noqa


__all__ = []


# adjust the path to import mermaidmro
import os
import sys
base = os.path.normpath(os.path.join(os.path.abspath(__file__), "../.."))
sys.path.append(base)
from mermaidmro import *

# import all tests
from .test_all import *
