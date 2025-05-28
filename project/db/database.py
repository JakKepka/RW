import sqlite3
import os
from typing import List, Dict, Optional

class DatabaseManager:
    def __init__(self, db_path: str = "db/problems.db"):
        self.db_path = db_path
        self._ensure_db_exists()
    
    def _ensure_db_exists(self):
        """Ensure database exists and has correct schema"""
        if not os.path.exists(self.db_path):
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            self._init_db()
    
    def _init_db(self):
        """Initialize database with schema"""
        # Get the directory where this file (database.py) is located
        current_dir = os.path.dirname(os.path.abspath(__file__))
        schema_path = os.path.join(current_dir, 'schema.sql')
        
        try:
            with open(schema_path, 'r') as f:
                schema = f.read()
            
            with sqlite3.connect(self.db_path) as conn:
                conn.executescript(schema)
                conn.commit()
        except FileNotFoundError:
            raise FileNotFoundError(f"Schema file not found at {schema_path}")
        except sqlite3.Error as e:
            raise sqlite3.Error(f"Database error while initializing: {str(e)}")
    
    def get_all_problems(self) -> List[Dict]:
        """Get all problems from database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, name, description, domain_definition, example_queries
                FROM problems
                ORDER BY name
            """)
            return [dict(row) for row in cursor.fetchall()]
    
    def get_problem(self, problem_id: int) -> Optional[Dict]:
        """Get a specific problem by ID"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, name, description, domain_definition, example_queries
                FROM problems
                WHERE id = ?
            """, (problem_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_problem_by_name(self, name: str) -> Optional[Dict]:
        """Get a specific problem by name"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, name, description, domain_definition, example_queries
                FROM problems
                WHERE name = ?
            """, (name,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def add_problem(self, name: str, description: str, domain_definition: str, example_queries: str) -> int:
        """Add a new problem to database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO problems (name, description, domain_definition, example_queries)
                VALUES (?, ?, ?, ?)
            """, (name, description, domain_definition, example_queries))
            conn.commit()
            return cursor.lastrowid
    
    def update_problem(self, problem_id: int, name: str, description: str, domain_definition: str, example_queries: str) -> bool:
        """Update an existing problem"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE problems
                SET name = ?, description = ?, domain_definition = ?, example_queries = ?
                WHERE id = ?
            """, (name, description, domain_definition, example_queries, problem_id))
            conn.commit()
            return cursor.rowcount > 0
    
    def delete_problem(self, problem_id: int) -> bool:
        """Delete a problem from database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM problems WHERE id = ?", (problem_id,))
            conn.commit()
            return cursor.rowcount > 0
    
    def search_problems(self, query: str) -> List[Dict]:
        """Search problems by name or description"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, name, description, domain_definition, example_queries
                FROM problems
                WHERE name LIKE ? OR description LIKE ?
                ORDER BY name
            """, (f"%{query}%", f"%{query}%"))
            return [dict(row) for row in cursor.fetchall()] 