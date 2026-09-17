"""Device identity generation."""

import secrets
from typing import Dict

PROFILES: Dict[str, Dict[str, str]] = {
    "pixel4": {"model": "Pixel 4", "manufacturer": "Google"},
    "pixel5": {"model": "Pixel 5", "manufacturer": "Google"},
    "pixel6": {"model": "Pixel 6", "manufacturer": "Google"},
    "s21":    {"model": "SM-G991B", "manufacturer": "samsung"},
    "s22":    {"model": "SM-S901B", "manufacturer": "samsung"},
}


class IdentityService:
    def generate(self, profile_id: str) -> dict:
        if profile_id not in PROFILES:
            raise ValueError(f"unknown profile: {profile_id}")
        p = PROFILES[profile_id]
        return {
            "android_id": secrets.token_hex(8),
            "imei": self._imei(),
            "mac_address": self._mac(),
            "serial": secrets.token_hex(8).upper(),
            "model": p["model"],
            "manufacturer": p["manufacturer"],
        }

    def _imei(self) -> str:
        partial = "35123456" + f"{secrets.randbelow(10**6):06d}"
        digits = [int(d) for d in partial]
        for i in range(len(digits) - 1, -1, -2):
            digits[i] *= 2
            if digits[i] > 9:
                digits[i] -= 9
        return partial + str((10 - sum(digits) % 10) % 10)

    def _mac(self) -> str:
        body = ":".join(f"{secrets.randbelow(256):02X}" for _ in range(3))
        return f"00:16:3E:{body}"
