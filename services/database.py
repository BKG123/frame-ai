import sqlite3
import json
from typing import Optional, List, Dict, Any
import hashlib


class AnalysisDatabase:
    def __init__(self, db_path: str = "analysis.db"):
        self.db_path = db_path
        self.init_db()

    def init_db(self):
        """Initialize the database with the required tables"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS analysis_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ip_address TEXT NOT NULL,
                    filename TEXT NOT NULL,
                    file_hash TEXT NOT NULL,
                    analysis_text TEXT NOT NULL,
                    exif_data TEXT,
                    image_path TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(ip_address, file_hash)
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_ip_address ON analysis_results(ip_address)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_file_hash ON analysis_results(file_hash)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_created_at ON analysis_results(created_at)
            """)
            conn.commit()

    def get_file_hash(self, file_path: str) -> str:
        """Generate a hash for the file content"""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    def get_filename_hash(self, file_path: str) -> str:
        """Generate a hash for the file content"""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    def get_content_hash(self, content: bytes) -> str:
        """Generate a hash for the file content from bytes"""
        return hashlib.md5(content).hexdigest()

    def store_analysis(
        self,
        ip_address: str,
        filename: str,
        file_hash: str,
        analysis_text: str,
        exif_data: Optional[Dict[str, Any]] = None,
        image_path: Optional[str] = None,
    ) -> int | None:
        """Store analysis result in the database"""
        exif_json = json.dumps(exif_data) if exif_data else None

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                INSERT OR REPLACE INTO analysis_results
                (ip_address, filename, file_hash, analysis_text, exif_data, image_path)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (ip_address, filename, file_hash, analysis_text, exif_json, image_path),
            )
            conn.commit()
            return cursor.lastrowid

    def get_analysis_by_ip(
        self, ip_address: str, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get all analysis results for a specific IP address"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                """
                SELECT id, filename, file_hash, analysis_text, exif_data, created_at
                FROM analysis_results
                WHERE ip_address = ?
                ORDER BY created_at DESC
                LIMIT ?
            """,
                (ip_address, limit),
            )

            results = []
            for row in cursor.fetchall():
                result = dict(row)
                if result["exif_data"]:
                    result["exif_data"] = json.loads(result["exif_data"])
                results.append(result)
            return results

    def get_analysis_by_hash(self, file_hash: str) -> Optional[Dict[str, Any]]:
        """Get analysis result by file hash"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                """
                SELECT id, ip_address, filename, analysis_text, exif_data, image_path, created_at
                FROM analysis_results
                WHERE file_hash = ?
                ORDER BY created_at DESC
                LIMIT 1
            """,
                (file_hash,),
            )

            row = cursor.fetchone()
            if row:
                result = dict(row)
                if result["exif_data"]:
                    result["exif_data"] = json.loads(result["exif_data"])
                return result
            return None

    def get_recent_analyses(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent analysis results across all users"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                """
                SELECT id, ip_address, filename, analysis_text, created_at
                FROM analysis_results
                ORDER BY created_at DESC
                LIMIT ?
            """,
                (limit,),
            )

            return [dict(row) for row in cursor.fetchall()]

    def delete_analysis(self, analysis_id: int, ip_address: str) -> bool:
        """Delete an analysis result (only if it belongs to the requesting IP)"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                DELETE FROM analysis_results
                WHERE id = ? AND ip_address = ?
            """,
                (analysis_id, ip_address),
            )
            conn.commit()
            return cursor.rowcount > 0


# Global database instance
db = AnalysisDatabase()
