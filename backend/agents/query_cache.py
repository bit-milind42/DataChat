import hashlib
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any


class QueryCache:
    """In-memory query result caching with TTL support"""
    
    def __init__(self, ttl_minutes: int = 60):
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.ttl = timedelta(minutes=ttl_minutes)
    
    @staticmethod
    def _generate_key(dataset_id: str, question: str) -> str:
        """Generate cache key from dataset_id and question"""
        combined = f"{dataset_id}::{question}".lower()
        return hashlib.sha256(combined.encode()).hexdigest()[:16]
    
    def get(self, dataset_id: str, question: str) -> Optional[Dict[str, Any]]:
        """Get cached result if exists and not expired"""
        key = self._generate_key(dataset_id, question)
        
        if key not in self.cache:
            return None
        
        entry = self.cache[key]
        
        # Check if expired
        if datetime.utcnow() > entry["expires_at"]:
            del self.cache[key]
            return None
        
        # Update last_accessed
        entry["last_accessed"] = datetime.utcnow().isoformat()
        entry["access_count"] += 1
        
        return {
            "result": entry["result"],
            "cached_at": entry["cached_at"],
            "hit": True
        }
    
    def set(self, dataset_id: str, question: str, result: Dict[str, Any]) -> None:
        """Store query result in cache"""
        key = self._generate_key(dataset_id, question)
        now = datetime.utcnow()
        
        self.cache[key] = {
            "result": result,
            "cached_at": now.isoformat(),
            "expires_at": now + self.ttl,
            "last_accessed": now.isoformat(),
            "access_count": 0,
            "dataset_id": dataset_id,
            "question": question
        }
    
    def clear_dataset(self, dataset_id: str) -> int:
        """Clear all cache entries for a dataset. Returns count cleared."""
        keys_to_delete = [
            key for key, entry in self.cache.items()
            if entry["dataset_id"] == dataset_id
        ]
        
        for key in keys_to_delete:
            del self.cache[key]
        
        return len(keys_to_delete)
    
    def clear_all(self) -> int:
        """Clear entire cache. Returns count cleared."""
        count = len(self.cache)
        self.cache.clear()
        return count
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_entries = len(self.cache)
        total_size = len(json.dumps(self.cache, default=str)) / 1024  # KB
        
        access_stats = {
            "total_entries": total_entries,
            "total_size_kb": round(total_size, 2),
            "datasets_cached": len(set(e["dataset_id"] for e in self.cache.values())),
            "avg_accesses_per_entry": round(
                sum(e["access_count"] for e in self.cache.values()) / total_entries
                if total_entries > 0 else 0,
                2
            )
        }
        
        return access_stats
    
    def get_dataset_cache_size(self, dataset_id: str) -> int:
        """Get number of cached queries for a dataset"""
        return sum(
            1 for entry in self.cache.values()
            if entry["dataset_id"] == dataset_id
        )


# Global cache instance
query_cache = QueryCache(ttl_minutes=60)
