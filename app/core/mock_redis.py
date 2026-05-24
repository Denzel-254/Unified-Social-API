"""Mock Redis for development when Redis is not available."""

import json
from typing import Any, Optional
from datetime import datetime, timedelta


class MockRedis:
    """Simple in-memory Redis replacement for development."""
    
    def __init__(self):
        self._data = {}
        self._expiry = {}
    
    def set(self, key: str, value: Any, ex: Optional[int] = None):
        """Set a value with optional expiration."""
        self._data[key] = json.dumps(value) if not isinstance(value, str) else value
        if ex:
            self._expiry[key] = datetime.utcnow() + timedelta(seconds=ex)
        return True
    
    def get(self, key: str):
        """Get a value."""
        # Check expiry
        if key in self._expiry:
            if datetime.utcnow() > self._expiry[key]:
                del self._data[key]
                del self._expiry[key]
                return None
        
        value = self._data.get(key)
        if value and isinstance(value, str):
            try:
                return json.loads(value)
            except:
                return value
        return value
    
    def delete(self, key: str):
        """Delete a value."""
        self._data.pop(key, None)
        self._expiry.pop(key, None)
        return 1
    
    def exists(self, key: str):
        """Check if key exists."""
        return 1 if key in self._data else 0
    
    def ping(self):
        """Ping the server."""
        return True
    
    def close(self):
        """Close connection."""
        pass


# Create a singleton instance
mock_redis = MockRedis()


def get_redis():
    """Get Redis client (mock if real not available)."""
    return mock_redis