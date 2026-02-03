import redis.asyncio as redis
import json
from config import Config

class MemoryStore:
    def __init__(self):
        self.redis = redis.Redis(
            host=Config.REDIS_HOST,
            port=Config.REDIS_PORT,
            password=Config.REDIS_PASSWORD,
            decode_responses=True
        )

    async def update_artifact_memory(self, session_id: str, new_artifacts: dict):
        """Append new high-value intel to the artifact memory set."""
        key = f"artifacts:{session_id}"
        # For simplicity, we store artifacts as a JSON blob or individual hash fields.
        # Here, adding to a set of found artifacts.
        if new_artifacts:
            for k, v in new_artifacts.items():
                if isinstance(v, list):
                    for item in v:
                        await self.redis.sadd(f"{key}:{k}", item)
                else:
                    await self.redis.sadd(f"{key}:{k}", v)

    async def get_artifacts(self, session_id: str) -> dict:
        """Retrieve all known artifacts for a session."""
        key_base = f"artifacts:{session_id}"
        # Matches ExtractedIntelligence keys + internal keys
        artifact_types = [
            "suspicious_links", "phone_numbers", "upi_ids", 
            "bankAccounts", "bankNames", "phishingLinks", "suspiciousKeywords"
        ]
        result = {}
        for a_type in artifact_types:
            items = await self.redis.smembers(f"{key_base}:{a_type}")
            result[a_type] = list(items)
        return result

    async def append_summary(self, session_id: str, summary_delta: str):
        """Append structured summary to the timeline."""
        key = f"summary:{session_id}"
        await self.redis.rpush(key, summary_delta)

    async def get_summary(self, session_id: str) -> list:
        """Get the full structured summary timeline."""
        key = f"summary:{session_id}"
        return await self.redis.lrange(key, 0, -1)

    async def increment_message_count(self, session_id: str) -> int:
        """Increment total messages exchanged."""
        key = f"msg_count:{session_id}"
        return await self.redis.incr(key)

    async def get_message_count(self, session_id: str) -> int:
        key = f"msg_count:{session_id}"
        val = await self.redis.get(key)
        return int(val) if val else 0

    async def mark_session_as_scam(self, session_id: str):
        """Mark a session as a confirmed scam."""
        key = f"scam_status:{session_id}"
        await self.redis.set(key, "1")

    async def is_session_scam(self, session_id: str) -> bool:
        """Check if session is already a confirmed scam."""
        key = f"scam_status:{session_id}"
        val = await self.redis.get(key)
        return val == "1"
