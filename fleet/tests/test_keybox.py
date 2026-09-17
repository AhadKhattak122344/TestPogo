import pytest
from fleet.keybox import Keybox, KeyboxManager, KeyboxUnavailable


class FakeRedis:
    def __init__(self):
        self.store = {}

    async def set(self, key, value):
        self.store[key] = value

    async def get(self, key):
        return self.store.get(key)


def make_manager(profile="pixel4", count=2):
    mgr = KeyboxManager("http://unused", FakeRedis())
    mgr.pool = {
        f"kb{i}": Keybox(f"kb{i}", b"<keybox/>", profile)
        for i in range(count)
    }
    return mgr


@pytest.mark.asyncio
async def test_assign():
    mgr = make_manager()
    kb = await mgr.assign("inst1", "pixel4")
    assert kb.uses == 1


@pytest.mark.asyncio
async def test_exhausted():
    mgr = make_manager(count=1)
    await mgr.assign("inst1", "pixel4")
    with pytest.raises(KeyboxUnavailable):
        await mgr.assign("inst2", "pixel4")


@pytest.mark.asyncio
async def test_rotate():
    mgr = make_manager(count=2)
    first = await mgr.assign("inst1", "pixel4")
    second = await mgr.rotate("inst1")
    assert first.keybox_id != second.keybox_id
