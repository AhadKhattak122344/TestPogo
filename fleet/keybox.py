"""Keybox pool management."""

from dataclasses import dataclass
from typing import Dict, List

import aiohttp


class KeyboxUnavailable(Exception):
    pass


@dataclass
class Keybox:
    keybox_id: str
    content: bytes
    profile: str
    uses: int = 0


class KeyboxManager:
    MAX_USES = 50
    ASSIGN_KEY = "keybox:assign:{instance_id}"

    def __init__(self, pool_url: str, redis_client):
        self.pool_url = pool_url
        self.redis = redis_client
        self.pool: Dict[str, Keybox] = {}
        self._assignments: Dict[str, str] = {}

    async def fetch_pool(self) -> List[Keybox]:
        async with aiohttp.ClientSession() as session:
            async with session.get(self.pool_url) as resp:
                resp.raise_for_status()
                data = await resp.json()
        self.pool = {
            item["id"]: Keybox(
                keybox_id=item["id"],
                content=item["content"].encode(),
                profile=item["profile"],
            )
            for item in data.get("keyboxes", [])
        }
        return list(self.pool.values())

    async def assign(self, instance_id: str, profile: str) -> Keybox:
        in_use = set(self._assignments.values())
        for kb in self.pool.values():
            if kb.profile == profile and kb.uses < self.MAX_USES \
               and kb.keybox_id not in in_use:
                kb.uses += 1
                self._assignments[instance_id] = kb.keybox_id
                await self.redis.set(
                    self.ASSIGN_KEY.format(instance_id=instance_id),
                    kb.keybox_id,
                )
                return kb
        raise KeyboxUnavailable(f"no keybox for profile={profile}")

    async def verify(self, instance_id: str) -> bool:
        return await self.redis.get(
            self.ASSIGN_KEY.format(instance_id=instance_id)
        ) is not None

    async def rotate(self, instance_id: str) -> Keybox:
        old_id = self._assignments.pop(instance_id, None)
        profile = "pixel4"
        if old_id and old_id in self.pool:
            profile = self.pool[old_id].profile
            self.pool[old_id].uses = self.MAX_USES
        return await self.assign(instance_id, profile)
