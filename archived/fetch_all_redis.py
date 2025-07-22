#!/usr/bin/env python3
"""
Fetch and display all keys and values from Redis.
Handles string and set types.
"""
import asyncio
import json
from app.core.config import redis_client

async def fetch_all_redis():
    print("🔍 Fetching all keys from Redis...")
    keys = await redis_client.keys("*")
    if not keys:
        print("No keys found in Redis.")
        return
    for key in keys:
        key_type = await redis_client.type(key)
        print(f"\nKey: {key} (type: {key_type})")
        if key_type == "string":
            value = await redis_client.get(key)
            try:
                value = json.loads(value)
            except Exception:
                pass
            print(f"  Value: {value}")
        elif key_type == "set":
            members = await redis_client.smembers(key)
            print(f"  Set members ({len(members)}):")
            for member in members:
                print(f"    - {member}")
        else:
            print("  [!] Unsupported type for display.")

if __name__ == "__main__":
    asyncio.run(fetch_all_redis()) 