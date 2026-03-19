#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OpenFOAM Expert Skill 缓存管理模块

功能:
1. 基于文件哈希的增量缓存
2. 支持内存缓存和文件缓存两级
3. 自动检测源码变更，失效缓存
4. 缓存统计和清理

使用方法:
    from cache_manager import CacheManager
    
    cache = CacheManager()
    
    # 获取或计算
    result = cache.get_or_compute("inheritance_fvMesh", compute_fn)
    
    # 直接操作
    cache.set("key", data)
    data = cache.get("key")
"""

import os
import sys
import json
import pickle
import hashlib
import time
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
from dataclasses import dataclass, field


@dataclass
class CacheEntry:
    """缓存条目"""
    key: str
    value: Any
    created_at: float
    expires_at: Optional[float] = None
    source_hash: Optional[str] = None
    size_bytes: int = 0
    hit_count: int = 0


class CacheManager:
    """
    缓存管理器
    
    支持两级缓存:
    1. 内存缓存: 快速访问，进程内有效
    2. 文件缓存: 持久化，跨进程共享
    """
    
    DEFAULT_TTL = 3600 * 24 * 7  # 默认缓存有效期: 7天
    MAX_MEMORY_CACHE_SIZE = 100  # 内存缓存最大条目数
    
    def __init__(self, cache_dir: str = None, ttl: float = None):
        """
        初始化缓存管理器
        
        Args:
            cache_dir: 缓存目录路径
            ttl: 缓存有效期（秒）
        """
        # 确定缓存目录
        if cache_dir:
            self.cache_dir = Path(cache_dir)
        else:
            script_dir = Path(__file__).parent
            skill_root = script_dir.parent
            self.cache_dir = skill_root / ".openfoam_cache"
            
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建子目录
        (self.cache_dir / "data").mkdir(exist_ok=True)
        (self.cache_dir / "index").mkdir(exist_ok=True)
        
        self.ttl = ttl or self.DEFAULT_TTL
        
        # 内存缓存
        self._memory_cache: Dict[str, CacheEntry] = {}
        self._source_hash_cache: Optional[str] = None
        
        # 统计信息
        self._stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0
        }
        
    def _compute_source_hash(self, src_dir: str = None) -> str:
        """
        计算源码目录哈希
        
        基于文件列表和修改时间，用于检测源码是否变更
        """
        if src_dir is None:
            # 使用默认源码路径
            script_dir = Path(__file__).parent
            skill_root = script_dir.parent
            src_dir = skill_root / "attachments" / "OpenFOAM" / "src"
            
        src_path = Path(src_dir)
        if not src_path.exists():
            return "no_source"
            
        # 收集关键文件的修改时间
        hash_data = []
        
        # 采样策略：只检查部分关键文件和目录结构
        key_directories = [
            "finiteVolume", "meshTools", "turbulenceModels",
            "thermophysicalModels", "transportModels"
        ]
        
        for key_dir in key_directories:
            dir_path = src_path / key_dir
            if dir_path.exists():
                # 获取目录下文件数量和最新修改时间
                try:
                    files = list(dir_path.rglob("*.H"))[:100]  # 采样100个文件
                    if files:
                        latest_mtime = max(f.stat().st_mtime for f in files)
                        file_count = len(list(dir_path.rglob("*.H")))
                        hash_data.append(f"{key_dir}:{file_count}:{latest_mtime}")
                except Exception:
                    pass
                    
        # 添加总文件数
        try:
            total_files = len(list(src_path.rglob("*.H")))
            hash_data.append(f"total:{total_files}")
        except Exception:
            pass
            
        hash_str = "|".join(hash_data)
        return hashlib.md5(hash_str.encode()).hexdigest()
    
    def _get_cache_path(self, key: str, suffix: str = ".pkl") -> Path:
        """获取缓存文件路径"""
        # 对键进行哈希，避免路径问题
        key_hash = hashlib.md5(key.encode()).hexdigest()
        return self.cache_dir / "data" / f"{key_hash}{suffix}"
    
    def _serialize(self, value: Any) -> bytes:
        """序列化值"""
        return pickle.dumps(value)
    
    def _deserialize(self, data: bytes) -> Any:
        """反序列化值"""
        return pickle.loads(data)
    
    def get(self, key: str) -> Optional[Any]:
        """
        获取缓存值
        
        Args:
            key: 缓存键
            
        Returns:
            缓存值，不存在返回 None
        """
        # 1. 检查内存缓存
        if key in self._memory_cache:
            entry = self._memory_cache[key]
            
            # 检查是否过期
            if entry.expires_at and time.time() > entry.expires_at:
                del self._memory_cache[key]
            else:
                entry.hit_count += 1
                self._stats["hits"] += 1
                return entry.value
        
        # 2. 检查文件缓存
        cache_path = self._get_cache_path(key)
        if cache_path.exists():
            try:
                with open(cache_path, 'rb') as f:
                    data = f.read()
                    
                entry = self._deserialize(data)
                
                # 检查是否过期
                if entry.expires_at and time.time() > entry.expires_at:
                    cache_path.unlink()
                else:
                    # 加载到内存缓存
                    self._add_to_memory_cache(key, entry)
                    entry.hit_count += 1
                    self._stats["hits"] += 1
                    return entry.value
                    
            except Exception:
                pass
                
        self._stats["misses"] += 1
        return None
    
    def set(self, key: str, value: Any, ttl: float = None) -> bool:
        """
        设置缓存值
        
        Args:
            key: 缓存键
            value: 缓存值
            ttl: 有效期（秒），None 使用默认值
            
        Returns:
            是否成功
        """
        try:
            expires_at = time.time() + (ttl or self.ttl)
            
            # 计算当前源码哈希
            source_hash = self._compute_source_hash()
            
            entry = CacheEntry(
                key=key,
                value=value,
                created_at=time.time(),
                expires_at=expires_at,
                source_hash=source_hash
            )
            
            # 序列化并计算大小
            data = self._serialize(entry)
            entry.size_bytes = len(data)
            
            # 写入文件缓存
            cache_path = self._get_cache_path(key)
            with open(cache_path, 'wb') as f:
                f.write(data)
                
            # 添加到内存缓存
            self._add_to_memory_cache(key, entry)
            
            return True
            
        except Exception as e:
            return False
    
    def _add_to_memory_cache(self, key: str, entry: CacheEntry):
        """添加到内存缓存，必要时淘汰旧条目"""
        # 检查容量
        if len(self._memory_cache) >= self.MAX_MEMORY_CACHE_SIZE:
            # 淘汰最少使用的条目
            lru_key = min(
                self._memory_cache.keys(),
                key=lambda k: self._memory_cache[k].hit_count
            )
            del self._memory_cache[lru_key]
            self._stats["evictions"] += 1
            
        self._memory_cache[key] = entry
    
    def get_or_compute(self, key: str, compute_fn: Callable[[], Any], 
                       ttl: float = None, force: bool = False) -> Any:
        """
        获取缓存或计算并缓存
        
        Args:
            key: 缓存键
            compute_fn: 计算函数
            ttl: 有效期
            force: 强制重新计算
            
        Returns:
            结果值
        """
        if not force:
            cached = self.get(key)
            if cached is not None:
                return cached
                
        # 计算新值
        value = compute_fn()
        self.set(key, value, ttl)
        return value
    
    def invalidate(self, key: str = None):
        """
        使缓存失效
        
        Args:
            key: 指定键，None 表示清除所有
        """
        if key:
            # 清除指定键
            if key in self._memory_cache:
                del self._memory_cache[key]
            cache_path = self._get_cache_path(key)
            if cache_path.exists():
                cache_path.unlink()
        else:
            # 清除所有
            self._memory_cache.clear()
            for cache_file in (self.cache_dir / "data").glob("*.pkl"):
                cache_file.unlink()
                
    def is_valid(self, key: str) -> bool:
        """
        检查缓存是否有效
        
        包括存在性和源码哈希匹配检查
        """
        # 检查内存缓存
        if key in self._memory_cache:
            entry = self._memory_cache[key]
            if entry.expires_at and time.time() > entry.expires_at:
                return False
            # 检查源码哈希
            current_hash = self._compute_source_hash()
            return entry.source_hash == current_hash
            
        # 检查文件缓存
        cache_path = self._get_cache_path(key)
        if not cache_path.exists():
            return False
            
        try:
            with open(cache_path, 'rb') as f:
                entry = self._deserialize(f.read())
                
            if entry.expires_at and time.time() > entry.expires_at:
                return False
                
            # 检查源码哈希
            current_hash = self._compute_source_hash()
            return entry.source_hash == current_hash
                
        except Exception:
            return False
    
    def get_stats(self) -> dict:
        """获取缓存统计信息"""
        total_requests = self._stats["hits"] + self._stats["misses"]
        hit_rate = self._stats["hits"] / total_requests if total_requests > 0 else 0
        
        # 计算缓存大小
        cache_size = 0
        file_count = 0
        for cache_file in (self.cache_dir / "data").glob("*.pkl"):
            cache_size += cache_file.stat().st_size
            file_count += 1
            
        return {
            "hits": self._stats["hits"],
            "misses": self._stats["misses"],
            "evictions": self._stats["evictions"],
            "hit_rate": f"{hit_rate:.2%}",
            "memory_cache_size": len(self._memory_cache),
            "file_cache_count": file_count,
            "total_cache_size_mb": round(cache_size / (1024 * 1024), 2)
        }
    
    def cleanup_expired(self) -> int:
        """
        清理过期缓存
        
        Returns:
            清理的条目数
        """
        cleaned = 0
        now = time.time()
        
        # 清理内存缓存
        expired_keys = [
            k for k, v in self._memory_cache.items()
            if v.expires_at and now > v.expires_at
        ]
        for key in expired_keys:
            del self._memory_cache[key]
            cleaned += 1
            
        # 清理文件缓存
        for cache_file in (self.cache_dir / "data").glob("*.pkl"):
            try:
                with open(cache_file, 'rb') as f:
                    entry = self._deserialize(f.read())
                if entry.expires_at and now > entry.expires_at:
                    cache_file.unlink()
                    cleaned += 1
            except Exception:
                pass
                
        return cleaned


# 便捷函数
_cache_manager: Optional[CacheManager] = None

def get_cache_manager() -> CacheManager:
    """获取全局缓存管理器实例"""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager()
    return _cache_manager


if __name__ == "__main__":
    # 测试缓存管理器
    cache = CacheManager()
    
    print("缓存目录:", cache.cache_dir)
    print("源码哈希:", cache._compute_source_hash())
    
    # 测试缓存
    test_key = "test_inheritance_fvMesh"
    test_value = {"class": "fvMesh", "base": ["polyMesh"]}
    
    print("\n设置缓存...")
    cache.set(test_key, test_value)
    
    print("获取缓存:", cache.get(test_key))
    
    print("\n缓存统计:", cache.get_stats())
    
    print("\n清理测试缓存...")
    cache.invalidate(test_key)
    print("清理后:", cache.get(test_key))
