from fleet.identity import IdentityService, PROFILES


def test_identity_format():
    svc = IdentityService()
    for p in PROFILES:
        i = svc.generate(p)
        assert len(i["android_id"]) == 16
        assert len(i["imei"]) == 15 and i["imei"].isdigit()
        assert i["mac_address"].startswith("00:16:3E:")
        assert len(i["serial"]) == 16
        assert i["model"] == PROFILES[p]["model"]
