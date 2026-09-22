"""Unit tests for root detection logic."""
import subprocess
from unittest.mock import MagicMock, patch

import pytest

from android_lab.root import RootManager, RootStatus


class TestRootStatus:
    def test_to_dict(self):
        status = RootStatus(
            serial="test-device",
            adb_uid=0,
            adb_root=True,
            emulator=True,
            debuggable=True,
            build_type="eng",
            abi="arm64-v8a",
            selinux="Permissive",
            magisk_binary="/sbin/magisk",
            modules=["module1", "module2"],
            observations=[],
        )
        result = status.to_dict()
        assert result["serial"] == "test-device"
        assert result["adb_uid"] == 0
        assert result["adb_root"] is True


def _setup_status_mocks(mock_adb, responses):
    """Helper to set up mock responses for status() calls.

    The status() method makes these calls in order:
    1. id -u
    2. getprop
    3. getenforce (optional - may fail)
    4. sh -c 'command -v magisk' (optional - may fail)
    5. ls -1 /data/adb/modules (if root)
    """
    def shell_side_effect(*args, **kwargs):
        # Handle id -u
        if len(args) >= 2 and args[0] == 'id' and '-u' in args:
            return responses.get('uid', '0\n')

        # Handle getprop
        if 'getprop' in args:
            return responses.get('getprop', '[ro.kernel.qemu]: [1]\n[ro.debuggable]: [1]\n')

        # Handle getenforce
        if 'getenforce' in args:
            if 'getenforce' in responses.get('errors', []):
                raise subprocess.SubprocessError("getenforce failed")
            return responses.get('getenforce', 'Permissive\n')

        # Handle magisk command check: sh -c 'command -v magisk'
        if len(args) >= 3 and args[0] == 'sh' and '-c' in args and 'magisk' in args[2]:
            if 'magisk_check' in responses.get('errors', []):
                raise subprocess.SubprocessError("magisk not found")
            return responses.get('magisk_path', '/sbin/magisk\n')

        # Handle ls for modules: ls -1 /data/adb/modules
        if 'ls' in args and '/data/adb/modules' in args:
            return responses.get('modules', 'module1\nmodule2\n')

        return ''

    mock_adb.shell.side_effect = shell_side_effect


class TestRootManagerStatus:
    @patch.object(RootManager, "__init__", lambda self, adb: setattr(self, "adb", adb))
    def test_status_basic_probes(self):
        manager = RootManager(None)
        manager.adb = MagicMock()
        _setup_status_mocks(manager.adb, {'uid': '0\n'})

        status = manager.status()
        assert status.adb_uid == 0
        assert status.adb_root is True
        assert status.emulator is True
        assert status.debuggable is True

    @patch.object(RootManager, "__init__", lambda self, adb: setattr(self, "adb", adb))
    def test_status_non_root(self):
        manager = RootManager(None)
        manager.adb = MagicMock()
        _setup_status_mocks(manager.adb, {'uid': '1023\n'})

        status = manager.status()
        assert status.adb_uid == 1023
        assert status.adb_root is False

    @patch.object(RootManager, "__init__", lambda self, adb: setattr(self, "adb", adb))
    def test_status_magisk_modules_when_root(self):
        manager = RootManager(None)
        manager.adb = MagicMock()
        _setup_status_mocks(manager.adb, {
            'uid': '0\n',
            'modules': 'module1\nmodule2\n',
            'magisk_path': '/sbin/magisk\n'
        })

        status = manager.status()
        assert status.modules is not None
        assert "module1" in status.modules

    @patch.object(RootManager, "__init__", lambda self, adb: setattr(self, "adb", adb))
    def test_status_unavailable_observations(self):
        manager = RootManager(None)
        manager.adb = MagicMock()
        _setup_status_mocks(manager.adb, {
            'uid': '0\n',
            'errors': ['getenforce']
        })

        status = manager.status()
        assert any('SELinux' in obs or 'unavailable' in obs.lower() for obs in status.observations)

    @patch.object(RootManager, "__init__", lambda self, adb: setattr(self, "adb", adb))
    def test_status_physical_device_detection(self):
        manager = RootManager(None)
        manager.adb = MagicMock()
        _setup_status_mocks(manager.adb, {
            'uid': '0\n',
            'getprop': '[ro.kernel.qemu]: [0]\n[ro.debuggable]: [0]\n'
        })

        status = manager.status()
        assert status.emulator is False
        assert status.debuggable is False
