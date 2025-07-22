#!/usr/bin/env python3
"""Simple Redis connection test with UUID-based character generation"""

import asyncio
import httpx
from dotenv import load_dotenv
from app.core.redis_client import redis_client
from app.core.llm import get_all_characters, get_all_conversation_ids, generate_characters_from_theme

async def test_redis_connection():
    """Test basic Redis operations with UUID-based characters"""
    print("🧪 Testing Redis Connection with UUID Characters...")
    
    try:
        # Test basic set/get
        await redis_client.redis_client.set('test_key', 'test_value')
        result = await redis_client.redis_client.get('test_key')
        print(f"✅ Basic set/get: {result}")
        
        # Test conversation storage
        test_data = {"id": "test123", "title": "Test Conversation", "messages": []}
        success = await redis_client.save_conversation("test123", test_data)
        print(f"✅ Save conversation: {success}")
        
        # Test conversation retrieval
        retrieved = await redis_client.get_conversation("test123")
        print(f"✅ Get conversation: {retrieved['title'] if retrieved else 'None'}")
        
        # Test character generation (UUIDs added automatically)
        print("🎭 Testing character generation with auto UUIDs...")
        
        response = await generate_characters_from_theme("coffee shop")
        print(f"✅ Generated {len(response.characters)} characters with UUIDs")
        
        for char in response.characters:
            print(f"  - {char.name} (ID: {char.id})")
        
        # Test character retrieval by UUID
        for char in response.characters:
            char_data = await redis_client.get_character(char.id)
            if char_data:
                print(f"✅ Retrieved character {char.name} from Redis")
            else:
                print(f"❌ Failed to retrieve character {char.name}")
        
        # Test global functions
        all_chars = await get_all_characters()
        all_convs = await get_all_conversation_ids()
        print(f"✅ Global functions: {len(all_chars)} characters, {len(all_convs)} conversations")
        
        # Test cleanup endpoint
        print("🧹 Testing cleanup endpoint...")
        async with httpx.AsyncClient() as client:
            response = await client.delete("http://localhost:8000/chat/cleanup")
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Cleanup endpoint: {result['message']}")
            else:
                print(f"❌ Cleanup endpoint failed: {response.status_code}")
        
        # Verify cleanup
        all_chars_after = await get_all_characters()
        all_convs_after = await get_all_conversation_ids()
        print(f"✅ After cleanup: {len(all_chars_after)} characters, {len(all_convs_after)} conversations")
        
        print("🎉 Redis connection test with UUIDs passed!")
        return True
        
    except Exception as e:
        print(f"❌ Redis test failed: {e}")
        return False

if __name__ == "__main__":
    load_dotenv()
    asyncio.run(test_redis_connection()) 