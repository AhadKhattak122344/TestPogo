#!/usr/bin/env python3
"""Device fingerprinting module for detecting emulated/virtualized environments."""

import os
import re
import json
import hashlib
import platform
import subprocess
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any


@dataclass
class DeviceFingerprint:
    device_id: str
    manufacturer: str
    model: str
    android_version: str
    sdk_level: int
    board: str
    product: str
    brand: str
    cpu_abi: str
    is_emulator: bool
    risk_score: int
    indicators: List[str] = field(default_factory=list)
    raw_props: Dict[str, str] = field(default_factory=dict)


EMULATOR_INDICATORS = {
    'generic': ['generic', 'sdk_google', 'android sdk'],
    'bluestacks': ['bluestacks', 'win8', 'win10', 'windows'],
    'nox': ['nox', 'tencent'],
    'memu': ['memu'],
    'ldplayer': ['ldplayer'],
    'mumu': ['mumu'],
    'redfinger': ['redfinger'],
    'vmos': ['vmos'],
    'emulator_hardware': ['goldfish', 'ranchu', 'cucumber', 'test'],
    'build_tags': ['eng.', 'test-keys', 'debug'],
    'qemu': ['qemu', 'vbox', 'virtualbox', 'vmware', 'hypervisor'],
}


def run_adb_shell(device: str, command: str) -> str:
    try:
        result = subprocess.run(
            ['adb', '-s', device, 'shell', command],
            capture_output=True, text=True, timeout=10
        )
        return result.stdout.strip()
    except Exception:
        return ''


def get_build_props(device: str) -> Dict[str, str]:
    raw = run_adb_shell(device, 'getprop')
    props = {}
    for line in raw.splitlines():
        m = re.match(r'\[([^\]]+)\]\s*:\s*\[([^\]]*)\]', line)
        if m:
            props[m.group(1)] = m.group(2)
    return props


def fingerprint_device(device: str) -> DeviceFingerprint:
    props = get_build_props(device)
    indicators = []
    risk_score = 0

    manufacturer = props.get('ro.product.manufacturer', 'unknown')
    model = props.get('ro.product.model', 'unknown')
    brand = props.get('ro.product.brand', 'unknown')
    product = props.get('ro.product.name', 'unknown')
    board = props.get('ro.board.platform', 'unknown')
    android_version = props.get('ro.build.version.release', 'unknown')
    sdk_level = int(props.get('ro.build.version.sdk', '0'))
    cpu_abi = props.get('ro.product.cpu_abi', 'unknown')

    all_text = f'{manufacturer} {model} {brand} {product} {board}'.lower()

    for category, patterns in EMULATOR_INDICATORS.items():
        for pattern in patterns:
            if pattern in all_text:
                indicators.append(f'{category}:{pattern}')
                risk_score += 15
                break

    build_tags = props.get('ro.build.tags', '').lower()
    if 'test-keys' in build_tags or 'debug' in build_tags:
        indicators.append('build:debug_tags')
        risk_score += 10

    if 'qemu' in all_text or 'hypervisor' in all_text:
        indicators.append('hypervisor:qemu')
        risk_score += 25

    is_emulator = risk_score >= 30

    device_id = hashlib.sha256(
        f'{manufacturer}:{model}:{product}:{board}:{sdk_level}'.encode()
    ).hexdigest()[:16]

    return DeviceFingerprint(
        device_id=device_id,
        manufacturer=manufacturer,
        model=model,
        android_version=android_version,
        sdk_level=sdk_level,
        board=board,
        product=product,
        brand=brand,
        cpu_abi=cpu_abi,
        is_emulator=is_emulator,
        risk_score=risk_score,
        indicators=indicators,
        raw_props=props,
    )


def list_devices() -> List[str]:
    try:
        result = subprocess.run(['adb', 'devices'], capture_output=True, text=True, timeout=10)
        devices = []
        for line in result.stdout.splitlines()[1:]:
            if '\tdevice' in line:
                devices.append(line.split('\t')[0])
        return devices
    except Exception:
        return []


def fingerprint_all() -> List[DeviceFingerprint]:
    return [fingerprint_device(d) for d in list_devices()]


def to_dict(fp: DeviceFingerprint) -> Dict[str, Any]:
    return {
        'device_id': fp.device_id,
        'manufacturer': fp.manufacturer,
        'model': fp.model,
        'android_version': fp.android_version,
        'sdk_level': fp.sdk_level,
        'board': fp.board,
        'product': fp.product,
        'brand': fp.brand,
        'cpu_abi': fp.cpu_abi,
        'is_emulator': fp.is_emulator,
        'risk_score': fp.risk_score,
        'indicators': fp.indicators,
    }


if __name__ == '__main__':
    devices = list_devices()
    if not devices:
        print('No ADB devices found')
    else:
        for d in devices:
            fp = fingerprint_device(d)
            print(json.dumps(to_dict(fp), indent=2))
