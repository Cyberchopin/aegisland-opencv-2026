"""Deny Internet socket connections in Python offline verification processes."""
import socket

_original_connect = socket.socket.connect
_original_connect_ex = socket.socket.connect_ex


def _deny_internet_connect(self, address):
    if self.family in (socket.AF_INET, socket.AF_INET6):
        raise RuntimeError("Offline verification forbids network connections")
    return _original_connect(self, address)


def _deny_internet_connect_ex(self, address):
    if self.family in (socket.AF_INET, socket.AF_INET6):
        raise RuntimeError("Offline verification forbids network connections")
    return _original_connect_ex(self, address)


socket.socket.connect = _deny_internet_connect
socket.socket.connect_ex = _deny_internet_connect_ex
