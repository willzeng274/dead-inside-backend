import json
from typing import Optional, Dict, Any, List
from app.core.config import redis_client as global_redis_client


class RedisClient:
    """Redis client for conversation and character storage"""
    
    def __init__(self):
        self.redis_client = global_redis_client
        self.conversation_prefix = "conversation:"
        self.character_prefix = "character:"
        self.character_list_key = "characters:list"
    
    def _get_conversation_key(self, conversation_id: str) -> str:
        """Get Redis key for a conversation"""
        return f"{self.conversation_prefix}{conversation_id}"
    
    async def save_conversation(self, conversation_id: str, conversation_data: Dict[str, Any]) -> bool:
        """Save a conversation to Redis"""
        try:
            key = self._get_conversation_key(conversation_id)
            serializable_data = self._prepare_for_serialization(conversation_data)
            serialized = json.dumps(serializable_data)
            return await self.redis_client.set(key, serialized)
        except Exception as e:
            print(f"Error saving conversation to Redis: {e}")
            return False
    
    async def get_conversation(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Get a conversation from Redis"""
        try:
            key = self._get_conversation_key(conversation_id)
            data = await self.redis_client.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            print(f"Error getting conversation from Redis: {e}")
            return None
    
    async def delete_conversation(self, conversation_id: str) -> bool:
        """Delete a conversation from Redis"""
        try:
            key = self._get_conversation_key(conversation_id)
            return bool(await self.redis_client.delete(key))
        except Exception as e:
            print(f"Error deleting conversation from Redis: {e}")
            return False
    
    async def get_all_conversation_keys(self) -> list[str]:
        """Get all conversation keys from Redis"""
        try:
            pattern = f"{self.conversation_prefix}*"
            keys = await self.redis_client.keys(pattern)
            return [key.replace(self.conversation_prefix, "") for key in keys]
        except Exception as e:
            print(f"Error getting conversation keys from Redis: {e}")
            return []

    def _get_character_key(self, character_id: str) -> str:
        """Get Redis key for a character"""
        return f"{self.character_prefix}{character_id}"

    async def save_character(self, character_id: str, character_data: Dict[str, Any]) -> bool:
        """Save a character to Redis"""
        try:
            key = self._get_character_key(character_id)
            serializable_data = self._prepare_for_serialization(character_data)
            serialized = json.dumps(serializable_data)
            success = await self.redis_client.set(key, serialized)
            
            if success:
                await self.redis_client.sadd(self.character_list_key, character_id)
            
            return success
        except Exception as e:
            print(f"Error saving character to Redis: {e}")
            return False

    async def get_character(self, character_id: str) -> Optional[Dict[str, Any]]:
        """Get a character from Redis"""
        try:
            key = self._get_character_key(character_id)
            data = await self.redis_client.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            print(f"Error getting character from Redis: {e}")
            return None

    async def get_all_characters(self) -> List[Dict[str, Any]]:
        """Get all characters from Redis"""
        try:
            character_ids = await self.redis_client.smembers(self.character_list_key)
            characters = []
            for char_id in character_ids:
                char_data = await self.get_character(char_id)
                if char_data:
                    characters.append(char_data)
            return characters
        except Exception as e:
            print(f"Error getting all characters from Redis: {e}")
            return []

    async def delete_character(self, character_id: str) -> bool:
        """Delete a character from Redis"""
        try:
            key = self._get_character_key(character_id)
            success = bool(await self.redis_client.delete(key))
            if success:
                await self.redis_client.srem(self.character_list_key, character_id)
            return success
        except Exception as e:
            print(f"Error deleting character from Redis: {e}")
            return False

    def _prepare_for_serialization(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare data for JSON serialization by converting datetime objects"""
        import copy
        serializable_data = copy.deepcopy(data)
        
        def convert_datetime(obj):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    if hasattr(value, 'isoformat'):
                        obj[key] = value.isoformat()
                    elif isinstance(value, (dict, list)):
                        convert_datetime(value)
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    if hasattr(item, 'isoformat'):
                        obj[i] = item.isoformat()
                    elif isinstance(item, (dict, list)):
                        convert_datetime(item)
        
        convert_datetime(serializable_data)
        return serializable_data


redis_client = RedisClient() 