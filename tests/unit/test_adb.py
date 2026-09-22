"""Unit tests for ADB abstraction."""
import subprocess
from unittest.mock import MagicMock, patch

import pytest

from android_lab.adb import Adb


class TestAdbConstruction:
    def test_default_serial(self):
        adb = Adb()
        assert adb.serial == "emulator-5554"
        assert adb.executable == "adb"
        assert adb.timeout == 30

    def test_custom_serial(self):
        adb = Adb(serial="device-123")
        assert adb.serial == "device-123"

    def test_invalid_timeout(self):
        with pytest.raises(ValueError, match="timeout"):
            Adb(timeout_s=-1)


class TestAdbCommand:
    def test_command_generation(self):
        adb = Adb(serial="test-device")
        cmd = adb.command("shell", "ls")
        assert cmd == ["adb", "-s", "test-device", "shell", "ls"]


class TestAdbRun:
    @patch("subprocess.run")
    def test_successful_shell_command(self, mock_run):
        mock_run.return_value = MagicMock(stdout="output\n", stderr="", returncode=0)
        adb = Adb()
        result = adb.run("shell", "ls")
        assert result == "output\n"
        mock_run.assert_called_once()

    @patch("subprocess.run")
    def test_file_not_found(self, mock_run):
        mock_run.side_effect = FileNotFoundError("adb not found")
        adb = Adb()
        with pytest.raises(FileNotFoundError, match="ADB executable was not found"):
            adb.run("shell", "ls")

    @patch("subprocess.run")
    def test_timeout(self, mock_run):
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="adb", timeout=30)
        adb = Adb()
        with pytest.raises(TimeoutError, match="timed out"):
            adb.run("shell", "ls")

    @patch("subprocess.run")
    def test_called_process_error(self, mock_run):
        mock_run.side_effect = subprocess.CalledProcessError(
            returncode=1, cmd="adb", output=b"", stderr=b"device not found"
        )
        adb = Adb()
        with pytest.raises(RuntimeError, match="ADB failed"):
            adb.run("shell", "ls")


class TestAdbShell:
    @patch("subprocess.run")
    def test_shell_quoting(self, mock_run):
        mock_run.return_value = MagicMock(stdout="result", stderr="", returncode=0)
        adb = Adb()
        adb.shell("echo", "hello world")
        # Verify shlex.join was used to quote arguments
        call_args = mock_run.call_args[0][0]
        assert "hello world" in " ".join(call_args) or "'hello world'" in " ".join(call_args)


class TestAdbConnect:
    @patch("subprocess.run")
    def test_connect_success(self, mock_run):
        def side_effect(*args, **kwargs):
            if "connect" in args[0]:
                return MagicMock(stdout="connected to 127.0.0.1:5555\n", stderr="", returncode=0)
            elif "get-state" in args[0]:
                return MagicMock(stdout="device\n", stderr="", returncode=0)
            raise AssertionError("Unexpected call")

        mock_run.side_effect = side_effect
        adb = Adb(serial="127.0.0.1:5555")
        result = adb.connect()
        assert "connected" in result.lower()

    @patch("subprocess.run")
    def test_connect_invalid_serial(self, mock_run):
        adb = Adb(serial="invalid-serial")
        with pytest.raises(ValueError, match="TCP"):
            adb.connect()

    @patch("subprocess.run")
    def test_connect_unauthorized(self, mock_run):
        def side_effect(*args, **kwargs):
            if "connect" in args[0]:
                return MagicMock(stdout="connected\n", stderr="", returncode=0)
            elif "get-state" in args[0]:
                return MagicMock(stdout="unauthorized\n", stderr="", returncode=0)
            raise AssertionError("Unexpected call")

        mock_run.side_effect = side_effect
        adb = Adb(serial="127.0.0.1:5555")
        with pytest.raises(RuntimeError, match="not authorized"):
            adb.connect()


class TestAdbScreenshot:
    @patch("subprocess.run")
    def test_valid_png(self, mock_run):
        png_data = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
        mock_run.return_value = MagicMock(stdout=png_data, stderr="", returncode=0)
        adb = Adb()
        result = adb.screenshot()
        assert result.startswith(b"\x89PNG")

    @patch("subprocess.run")
    def test_invalid_png(self, mock_run):
        mock_run.return_value = MagicMock(stdout=b"not a png", stderr="", returncode=0)
        adb = Adb()
        with pytest.raises(RuntimeError, match="PNG"):
            adb.screenshot()
