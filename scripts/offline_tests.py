"""Run tests with outbound sockets disabled, after dependency installation."""
import socket
import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def blocked(*args, **kwargs):
    raise AssertionError('network access is forbidden during offline tests')

socket.create_connection = blocked
socket.socket.connect = blocked
socket.socket.connect_ex = blocked
suite = unittest.defaultTestLoader.discover('tests')
result = unittest.TextTestRunner(verbosity=2).run(suite)
raise SystemExit(not result.wasSuccessful())
