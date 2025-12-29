#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Memory Persistence Layer - File system storage for long-term memory (10GB+)
Handles backups, archiving, compression, and vector index persistence
"""

import os
import json
import gzip
import shutil
import pickle
import threading
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from .helpers import log_info, log_warning, log_error
from .memory import get_memory_system, LTM_STORAGE_ROOT, VECTOR_INDEX_PATH, BACKUP_PATH


# ═══════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════

# Backup settings
BACKUP_RETENTION_DAYS = 30
BACKUP_COMPRESSION = True
BACKUP_INCREMENTAL = True

# Archive settings
ARCHIVE_AGE_DAYS = 90  # Archive memories older than this
ARCHIVE_COMPRESSION_LEVEL = 9

# Storage paths
ARCHIVE_PATH = os.path.join(LTM_STORAGE_ROOT, "archives")
TEMP_PATH = os.path.join(LTM_STORAGE_ROOT, "temp")

# Create directories
for p in [ARCHIVE_PATH, TEMP_PATH]:
    Path(p).mkdir(parents=True, exist_ok=True)


# ═══════════════════════════════════════════════════════════════════
# BACKUP MANAGER
# ═══════════════════════════════════════════════════════════════════

class MemoryBackupManager:
    """Handles automated backups of memory database and indices"""
    
    def __init__(self):
        self._lock = threading.Lock()
        self.last_backup_time = 0
    
    def create_backup(self, compress: bool = BACKUP_COMPRESSION) -> Dict[str, Any]:
        """
        Create full backup of memory system
        
        Returns:
            Dict with backup details (path, size, timestamp)
        """
        with self._lock:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"memory_backup_{timestamp}"
            backup_dir = os.path.join(BACKUP_PATH, backup_name)
            
            try:
                # Create backup directory
                Path(backup_dir).mkdir(parents=True, exist_ok=True)
                
                # 1. Backup SQLite database
                mem = get_memory_system()
                db_backup_path = os.path.join(backup_dir, "memory.db")
                
                with mem.db._conn() as conn:
                    # Use SQLite backup API for consistency
                    backup_conn = mem.db._conn()
                    backup_conn.execute("BEGIN IMMEDIATE")
                    conn.backup(backup_conn)
                    backup_conn.commit()
                    backup_conn.close()
                
                shutil.copy2(mem.db.db_path, db_backup_path)
                
                # 2. Backup vector indices (if exist)
                if os.path.exists(VECTOR_INDEX_PATH):
                    vector_backup = os.path.join(backup_dir, "vector_indices")
                    shutil.copytree(VECTOR_INDEX_PATH, vector_backup, dirs_exist_ok=True)
                
                # 3. Create metadata file
                metadata = {
                    "timestamp": timestamp,
                    "backup_time": time.time(),
                    "db_size_mb": os.path.getsize(db_backup_path) / 1024 / 1024,
                    "compressed": compress
                }
                
                with open(os.path.join(backup_dir, "metadata.json"), "w") as f:
                    json.dump(metadata, f, indent=2)
                
                # 4. Compress if requested
                if compress:
                    compressed_path = f"{backup_dir}.tar.gz"
                    shutil.make_archive(backup_dir, "gztar", BACKUP_PATH, backup_name)
                    shutil.rmtree(backup_dir)
                    backup_path = compressed_path
                    metadata["compressed_size_mb"] = os.path.getsize(compressed_path) / 1024 / 1024
                else:
                    backup_path = backup_dir
                
                self.last_backup_time = time.time()
                
                log_info(f"Created memory backup: {backup_path}", "PERSISTENCE")
                
                return {
                    "success": True,
                    "backup_path": backup_path,
                    "metadata": metadata
                }
                
            except Exception as e:
                log_error(e, "BACKUP_CREATE")
                # Cleanup failed backup
                if os.path.exists(backup_dir):
                    shutil.rmtree(backup_dir)
                return {
                    "success": False,
                    "error": str(e)
                }
    
    def cleanup_old_backups(self, retention_days: int = BACKUP_RETENTION_DAYS) -> Dict[str, Any]:
        """
        Delete backups older than retention period
        
        Args:
            retention_days: Keep backups newer than this many days
            
        Returns:
            Dict with cleanup statistics
        """
        cutoff_time = time.time() - (retention_days * 24 * 3600)
        deleted_count = 0
        freed_mb = 0
        
        try:
            for item in os.listdir(BACKUP_PATH):
                item_path = os.path.join(BACKUP_PATH, item)
                
                # Check if old enough
                if os.path.getmtime(item_path) < cutoff_time:
                    # Calculate size
                    if os.path.isfile(item_path):
                        freed_mb += os.path.getsize(item_path) / 1024 / 1024
                        os.remove(item_path)
                    elif os.path.isdir(item_path):
                        for root, dirs, files in os.walk(item_path):
                            for f in files:
                                freed_mb += os.path.getsize(os.path.join(root, f)) / 1024 / 1024
                        shutil.rmtree(item_path)
                    
                    deleted_count += 1
            
            log_info(f"Cleaned up {deleted_count} old backups, freed {freed_mb:.2f} MB", "PERSISTENCE")
            
            return {
                "success": True,
                "deleted_count": deleted_count,
                "freed_mb": round(freed_mb, 2)
            }
            
        except Exception as e:
            log_error(e, "BACKUP_CLEANUP")
            return {
                "success": False,
                "error": str(e)
            }
    
    def restore_backup(self, backup_path: str) -> Dict[str, Any]:
        """
        Restore memory system from backup
        
        **CAUTION:** This will overwrite current memory database!
        
        Args:
            backup_path: Path to backup file or directory
            
        Returns:
            Dict with restoration status
        """
        try:
            mem = get_memory_system()
            
            # Stop background tasks
            mem.stop_background_tasks()
            
            # Extract if compressed
            if backup_path.endswith(".tar.gz"):
                extract_dir = os.path.join(TEMP_PATH, f"restore_{int(time.time())}")
                shutil.unpack_archive(backup_path, extract_dir)
                backup_dir = os.path.join(extract_dir, os.listdir(extract_dir)[0])
            else:
                backup_dir = backup_path
            
            # Restore database
            db_backup = os.path.join(backup_dir, "memory.db")
            if os.path.exists(db_backup):
                shutil.copy2(db_backup, mem.db.db_path)
            else:
                raise FileNotFoundError("memory.db not found in backup")
            
            # Restore vector indices
            vector_backup = os.path.join(backup_dir, "vector_indices")
            if os.path.exists(vector_backup):
                if os.path.exists(VECTOR_INDEX_PATH):
                    shutil.rmtree(VECTOR_INDEX_PATH)
                shutil.copytree(vector_backup, VECTOR_INDEX_PATH)
            
            # Clear caches
            mem.cache.clear()
            
            # Restart background tasks
            mem.start_background_tasks()
            
            log_info(f"Restored memory from backup: {backup_path}", "PERSISTENCE")
            
            return {
                "success": True,
                "backup_path": backup_path,
                "restored_at": time.time()
            }
            
        except Exception as e:
            log_error(e, "BACKUP_RESTORE")
            return {
                "success": False,
                "error": str(e)
            }


# ═══════════════════════════════════════════════════════════════════
# ARCHIVE MANAGER
# ═══════════════════════════════════════════════════════════════════

class MemoryArchiveManager:
    """Handles archiving of old memories to filesystem"""
    
    def __init__(self):
        self._lock = threading.Lock()
    
    def archive_old_memories(self, age_days: int = ARCHIVE_AGE_DAYS,
                             user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Archive old memories to compressed files
        
        Args:
            age_days: Archive memories older than this
            user_id: Optional user ID to archive (default: all users)
            
        Returns:
            Dict with archiving statistics
        """
        with self._lock:
            cutoff_time = time.time() - (age_days * 24 * 3600)
            mem = get_memory_system()
            
            try:
                # Get old memories from DB
                with mem.db._conn() as conn:
                    query = """
                        SELECT * FROM memory_nodes 
                        WHERE created_at < ? AND deleted = 0
                    """
                    params = [cutoff_time]
                    
                    if user_id:
                        query += " AND user_id = ?"
                        params.append(user_id)
                    
                    rows = conn.execute(query, params).fetchall()
                
                if not rows:
                    return {
                        "success": True,
                        "archived_count": 0,
                        "message": "No old memories to archive"
                    }
                
                # Group by user and month
                grouped_memories: Dict[str, Dict[str, List]] = {}
                for row in rows:
                    uid = row["user_id"]
                    created_dt = datetime.fromtimestamp(row["created_at"])
                    month_key = created_dt.strftime("%Y_%m")
                    
                    if uid not in grouped_memories:
                        grouped_memories[uid] = {}
                    if month_key not in grouped_memories[uid]:
                        grouped_memories[uid][month_key] = []
                    
                    grouped_memories[uid][month_key].append(dict(row))
                
                # Archive each group
                total_archived = 0
                for uid, months in grouped_memories.items():
                    user_archive_dir = os.path.join(ARCHIVE_PATH, uid)
                    Path(user_archive_dir).mkdir(parents=True, exist_ok=True)
                    
                    for month_key, memories in months.items():
                        archive_file = os.path.join(user_archive_dir, f"memories_{month_key}.json.gz")
                        
                        # Write compressed JSON
                        with gzip.open(archive_file, "wt", encoding="utf-8", compresslevel=ARCHIVE_COMPRESSION_LEVEL) as f:
                            json.dump(memories, f, ensure_ascii=False, indent=2)
                        
                        total_archived += len(memories)
                        
                        # Mark as archived in DB (soft delete)
                        with mem.db._conn() as conn:
                            memory_ids = [m["id"] for m in memories]
                            placeholders = ",".join("?" * len(memory_ids))
                            conn.execute(f"UPDATE memory_nodes SET deleted=1 WHERE id IN ({placeholders})", memory_ids)
                            conn.commit()
                
                log_info(f"Archived {total_archived} old memories", "PERSISTENCE")
                
                return {
                    "success": True,
                    "archived_count": total_archived,
                    "users_affected": len(grouped_memories)
                }
                
            except Exception as e:
                log_error(e, "ARCHIVE")
                return {
                    "success": False,
                    "error": str(e)
                }
    
    def retrieve_archived_memories(self, user_id: str, year: int, month: int) -> List[Dict[str, Any]]:
        """
        Retrieve archived memories for specific month
        
        Args:
            user_id: User ID
            year: Year (YYYY)
            month: Month (1-12)
            
        Returns:
            List of archived memories
        """
        try:
            month_key = f"{year}_{month:02d}"
            archive_file = os.path.join(ARCHIVE_PATH, user_id, f"memories_{month_key}.json.gz")
            
            if not os.path.exists(archive_file):
                return []
            
            with gzip.open(archive_file, "rt", encoding="utf-8") as f:
                memories = json.load(f)
            
            log_info(f"Retrieved {len(memories)} archived memories for {user_id}/{month_key}", "PERSISTENCE")
            return memories
            
        except Exception as e:
            log_error(e, "ARCHIVE_RETRIEVE")
            return []


# ═══════════════════════════════════════════════════════════════════
# STORAGE MONITOR
# ═══════════════════════════════════════════════════════════════════

class StorageMonitor:
    """Monitors storage usage and provides alerts"""
    
    @staticmethod
    def get_storage_stats() -> Dict[str, Any]:
        """Get comprehensive storage statistics"""
        try:
            stats = {
                "ltm_storage_root": LTM_STORAGE_ROOT,
                "total_size_mb": 0,
                "breakdown": {}
            }
            
            # Calculate sizes for each directory
            for name, path in [
                ("database", get_memory_system().db.db_path),
                ("vector_indices", VECTOR_INDEX_PATH),
                ("backups", BACKUP_PATH),
                ("archives", ARCHIVE_PATH)
            ]:
                if os.path.exists(path):
                    size_mb = StorageMonitor._get_dir_size(path) / 1024 / 1024
                    stats["breakdown"][name] = {
                        "path": path,
                        "size_mb": round(size_mb, 2)
                    }
                    stats["total_size_mb"] += size_mb
            
            stats["total_size_mb"] = round(stats["total_size_mb"], 2)
            stats["total_size_gb"] = round(stats["total_size_mb"] / 1024, 2)
            
            # Check if approaching limits
            if stats["total_size_gb"] > 8:
                stats["warning"] = "Storage usage exceeds 8GB, consider archiving old memories"
            
            return stats
            
        except Exception as e:
            log_error(e, "STORAGE_STATS")
            return {"error": str(e)}
    
    @staticmethod
    def _get_dir_size(path: str) -> int:
        """Calculate total size of directory in bytes"""
        total_size = 0
        
        if os.path.isfile(path):
            return os.path.getsize(path)
        
        for dirpath, dirnames, filenames in os.walk(path):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                if os.path.exists(filepath):
                    total_size += os.path.getsize(filepath)
        
        return total_size


# ═══════════════════════════════════════════════════════════════════
# AUTOMATED BACKGROUND TASKS
# ═══════════════════════════════════════════════════════════════════

class PersistenceBackgroundTasks:
    """Runs automated backup and archiving tasks"""
    
    def __init__(self):
        self.backup_manager = MemoryBackupManager()
        self.archive_manager = MemoryArchiveManager()
        self._running = False
        self._backup_thread = None
        self._archive_thread = None
    
    def start(self) -> None:
        """Start background persistence tasks"""
        if self._running:
            return
        
        self._running = True
        
        # Backup task (daily)
        def backup_loop():
            while self._running:
                try:
                    time.sleep(86400)  # 24 hours
                    self.backup_manager.create_backup()
                    self.backup_manager.cleanup_old_backups()
                except Exception as e:
                    log_error(e, "BACKUP_TASK")
        
        # Archive task (weekly)
        def archive_loop():
            while self._running:
                try:
                    time.sleep(604800)  # 7 days
                    self.archive_manager.archive_old_memories()
                except Exception as e:
                    log_error(e, "ARCHIVE_TASK")
        
        self._backup_thread = threading.Thread(target=backup_loop, daemon=True)
        self._archive_thread = threading.Thread(target=archive_loop, daemon=True)
        
        self._backup_thread.start()
        self._archive_thread.start()
        
        log_info("Persistence background tasks started", "PERSISTENCE")
    
    def stop(self) -> None:
        """Stop background tasks"""
        self._running = False
        log_info("Persistence background tasks stopped", "PERSISTENCE")


# ═══════════════════════════════════════════════════════════════════
# GLOBAL INSTANCE
# ═══════════════════════════════════════════════════════════════════

_persistence_tasks: Optional[PersistenceBackgroundTasks] = None

def get_persistence_tasks() -> PersistenceBackgroundTasks:
    """Get global persistence tasks instance"""
    global _persistence_tasks
    if _persistence_tasks is None:
        _persistence_tasks = PersistenceBackgroundTasks()
        _persistence_tasks.start()
    return _persistence_tasks


# Auto-start on module import
get_persistence_tasks()

log_info("Memory persistence layer initialized", "PERSISTENCE")
