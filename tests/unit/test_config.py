"""Unit tests for configuration loading."""
import os
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from android_lab import config


class TestPackageName:
    def test_valid_package(self):
        assert config.package_name("com.example.app") == "com.example.app"

    def test_invalid_package(self):
        with pytest.raises(ValueError, match="Invalid Android package"):
            config.package_name("invalid")
        with pytest.raises(ValueError, match="Invalid Android package"):
            config.package_name("123.com.app")


class TestComponent:
    def test_valid_component(self):
        result = config.component("com.example.app/.MainActivity")
        assert result == "com.example.app/.MainActivity"

    def test_invalid_component(self):
        with pytest.raises(ValueError, match="Invalid Android component"):
            config.component("invalid")

    def test_package_mismatch(self):
        with pytest.raises(ValueError, match="must belong to"):
            config.component("com.other.app/.MainActivity", package="com.example.app")


class TestPositiveNumber:
    def test_valid_positive(self):
        config.positive_number(10, "test")
        config.positive_number(0.5, "test")

    def test_invalid_non_positive(self):
        with pytest.raises(ValueError, match="positive"):
            config.positive_number(0, "test")
        with pytest.raises(ValueError, match="positive"):
            config.positive_number(-1, "test")

    def test_invalid_non_numeric(self):
        with pytest.raises(ValueError, match="positive"):
            config.positive_number("ten", "test")
        with pytest.raises(ValueError, match="positive"):
            config.positive_number(True, "test")


class TestConfigLoad:
    @pytest.fixture
    def valid_config_data(self):
        return {
            "profile": "test",
            "profiles": {"test": {"accel": "on", "gpu": "swiftshader_indirect"}},
            "adb": {
                "executable": "adb",
                "serial": "emulator-5554",
                "server": "tcp:127.0.0.1:5037",
                "timeout_s": 30,
            },
            "emulator": {"api": 34, "avd": "test", "boot_timeout_s": 600},
            "app": {
                "package": "com.example.app",
                "activity": "com.example.app/.MainActivity",
                "ready_activity": None,
            },
            "location": {"backend": "geo"},
        }

    def test_load_valid_config(self, tmp_path, valid_config_data):
        config_file = tmp_path / "test.yaml"
        config_file.write_text(yaml.dump(valid_config_data))
        result = config.load(config_file)
        assert result["app"]["package"] == "com.example.app"
        assert result["adb"]["serial"] == "emulator-5554"

    def test_load_invalid_yaml(self, tmp_path):
        config_file = tmp_path / "invalid.yaml"
        config_file.write_text("not: valid: yaml: :")
        with pytest.raises(ValueError, match="Invalid YAML"):
            config.load(config_file)

    def test_load_non_mapping(self, tmp_path):
        config_file = tmp_path / "non_mapping.yaml"
        config_file.write_text("- list\n- not\n- mapping\n")
        with pytest.raises(ValueError, match="YAML mapping"):
            config.load(config_file)

    def test_missing_required_fields(self, tmp_path):
        config_file = tmp_path / "missing.yaml"
        config_file.write_text("app: {}\nemulator: {}\nadb: {}\nlocation: {}\nprofiles: {}\n")
        with pytest.raises(ValueError, match="Missing configuration field"):
            config.load(config_file)

    def test_env_override_serial(self, tmp_path, valid_config_data):
        config_file = tmp_path / "test.yaml"
        config_file.write_text(yaml.dump(valid_config_data))
        with patch.dict(os.environ, {"LAB_SERIAL": "custom-device"}):
            result = config.load(config_file)
            assert result["adb"]["serial"] == "custom-device"

    def test_env_override_server(self, tmp_path, valid_config_data):
        config_file = tmp_path / "test.yaml"
        config_file.write_text(yaml.dump(valid_config_data))
        with patch.dict(os.environ, {"ADB_SERVER_SOCKET": "tcp:192.168.1.1:5037"}):
            result = config.load(config_file)
            assert result["adb"]["server"] == "tcp:192.168.1.1:5037"

    def test_invalid_profile(self, tmp_path, valid_config_data):
        valid_config_data["profile"] = "nonexistent"
        config_file = tmp_path / "test.yaml"
        config_file.write_text(yaml.dump(valid_config_data))
        with pytest.raises(ValueError, match="Unknown emulator profile"):
            config.load(config_file)

    def test_invalid_location_backend(self, tmp_path, valid_config_data):
        valid_config_data["location"]["backend"] = "unsupported"
        config_file = tmp_path / "test.yaml"
        config_file.write_text(yaml.dump(valid_config_data))
        with pytest.raises(ValueError, match="location.backend"):
            config.load(config_file)


class TestDefaultPath:
    def test_fallback_to_module_default(self):
        # When config/default.yaml doesn't exist, should fall back to android_lab/default.yaml
        path = config.default_path()
        assert path.exists()
        assert path.name == "default.yaml"
