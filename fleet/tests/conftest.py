"""Test conftest - provides mock libvirt for Windows dev."""

import sys
import types
from unittest.mock import MagicMock


def setup_mock_libvirt():
    if "libvirt" in sys.modules:
        return

    libvirt = types.ModuleType("libvirt")

    libvirt.VIR_DOMAIN_ACTIVE = 1
    libvirt.VIR_DOMAIN_INACTIVE = 0
    libvirt.VIR_DOMAIN_UNDEFINE_NVRAM = 1
    libvirt.VIR_DOMAIN_UNDEFINE_MANAGED_SAVE = 2
    libvirt.libvirtError = type("libvirtError", (Exception,), {})

    class MockDomain:
        def __init__(self, name="mock"):
            self.name = name
            self._active = False

        def isActive(self):
            return self._active

        def create(self):
            self._active = True
            return 0

        def destroy(self):
            self._active = False
            return 0

        def undefineFlags(self, flags):
            pass

    class MockConnection:
        def __init__(self, *args, **kwargs):
            pass

        def defineXML(self, xml):
            return MagicMock()

        def lookupByName(self, name):
            return MockDomain(name)

    libvirt.open = MagicMock(return_value=MockConnection())

    sys.modules["libvirt"] = libvirt


setup_mock_libvirt()
