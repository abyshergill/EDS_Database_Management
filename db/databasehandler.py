import sqlite3
import logging
import hashlib
# import psycopg2                   # Uncomment for PostgreSQL support

logger = logging.getLogger(__name__)

class DatabaseHandler:
    def __init__(self, config_manager):
        self.config = config_manager
        self.db_type = self.config.get("database.type", "sqlite")
        
        if self.db_type == "sqlite":
            self.db_path = self.config.get("database.sqlite_path", "eds.db")
            self.init_sqlite()
        # Uncomment for PostgreSQL support
        # elif self.db_type == "postgresql":
        #     self.pg_config = self.config.get("database.postgresql", {})
        #     self.init_postgresql()
        else:
            raise ValueError(f"Unsupported database type: {self.db_type}")

    def init_sqlite(self):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS eds (
                rowid INTEGER PRIMARY KEY AUTOINCREMENT,
                component TEXT NOT NULL,
                vhx_remark TEXT,
                vhx_data BLOB,
                eds_remark TEXT,
                eds_data BLOB,
                remark TEXT,
                created_by TEXT,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                modified_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (created_by) REFERENCES users(username)
            )
            """)
            
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                table_name TEXT,
                operation TEXT,
                record_id INTEGER,
                user_id TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                details TEXT
            )
            """)
            
            conn.commit()
            conn.close()
            logger.info("SQLite database initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing SQLite: {e}")
            raise

    # Uncomment for PostgreSQL support
    # def init_postgresql(self):
    #     try:
    #         conn = psycopg2.connect(**self.pg_config)
    #         cursor = conn.cursor()
    #         
    #         # Create users table
    #         cursor.execute("""
    #         CREATE TABLE IF NOT EXISTS users (
    #             id SERIAL PRIMARY KEY,
    #             username VARCHAR(50) UNIQUE NOT NULL,
    #             password_hash VARCHAR(255) NOT NULL,
    #             created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    #         )
    #         """)
    #         cursor.execute("""
    #         CREATE TABLE IF NOT EXISTS eds (
    #             rowid SERIAL PRIMARY KEY,
    #             component TEXT NOT NULL,
    #             vhx_remark TEXT,
    #             vhx_data BYTEA,
    #             eds_remark TEXT,
    #             eds_data BYTEA,
    #             remark TEXT,
    #             created_by VARCHAR(50),
    #             created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    #             modified_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    #             FOREIGN KEY (created_by) REFERENCES users(username)
    #         )
    #         """)
    #         
    #         conn.commit()
    #         conn.close()
    #         logging.info("PostgreSQL database initialized successfully")
    #         
    #     except Exception as e:
    #         logging.error(f"Error initializing PostgreSQL: {e}")
    #         raise

    def hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()

    def create_user(self, username, password):
        if self.db_type == "sqlite":
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            try:
                password_hash = self.hash_password(password)
                cursor.execute("""
                INSERT INTO users (username, password_hash)
                VALUES (?, ?)
                """, (username, password_hash))
                conn.commit()
                logging.info(f"User {username} created successfully")
            except sqlite3.IntegrityError:
                raise Exception("Username already exists")
            finally:
                conn.close()

    def verify_user(self, username, password):
        if self.db_type == "sqlite":
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            try:
                password_hash = self.hash_password(password)
                cursor.execute("""
                SELECT id FROM users 
                WHERE username = ? AND password_hash = ?
                """, (username, password_hash))
                
                result = cursor.fetchone()
                return result is not None
            finally:
                conn.close()

    def add_entry(self, component, vhx_remark, vhx_data, eds_remark, eds_data, remark, created_by):
        if self.db_type == "sqlite":
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            try:
                cursor.execute("""
                INSERT INTO eds (component, vhx_remark, vhx_data, eds_remark, eds_data, remark, created_by)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (component, vhx_remark, vhx_data, eds_remark, eds_data, remark, created_by))
                conn.commit()
                logging.info(f"Entry added by {created_by}: {component}")
            finally:
                conn.close()

    def update_entry(self, rowid, component, vhx_remark, vhx_data, eds_remark, eds_data, remark):
        if self.db_type == "sqlite":
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            try:
                cursor.execute("""
                UPDATE eds
                SET component = ?, vhx_remark = ?, vhx_data = ?, eds_remark = ?, 
                    eds_data = ?, remark = ?, modified_date = CURRENT_TIMESTAMP
                WHERE rowid = ?
                """, (component, vhx_remark, vhx_data, eds_remark, eds_data, remark, rowid))
                conn.commit()
                logging.info(f"Entry updated: ID {rowid}")
            finally:
                conn.close()

    def delete_entry(self, rowid):
        if self.db_type == "sqlite":
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            try:
                cursor.execute("DELETE FROM eds WHERE rowid = ?", (rowid,))
                conn.commit()
                logging.info(f"Entry deleted: ID {rowid}")
            finally:
                conn.close()

    def get_all_entries(self):
        if self.db_type == "sqlite":
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            try:
                cursor.execute("""
                SELECT rowid, component, vhx_remark, vhx_data, eds_remark, 
                       eds_data, remark, created_by, created_date
                FROM eds
                ORDER BY created_date DESC
                """)
                return cursor.fetchall()
            finally:
                conn.close()

    def get_entry_by_id(self, rowid):
        if self.db_type == "sqlite":
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            try:
                cursor.execute("""
                SELECT rowid, component, vhx_remark, vhx_data, eds_remark, 
                       eds_data, remark, created_by, created_date
                FROM eds WHERE rowid = ?
                """, (rowid,))
                return cursor.fetchone()
            finally:
                conn.close()

    def search_by_component(self, component_name):
        if self.db_type == "sqlite":
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            try:
                cursor.execute("""
                SELECT rowid, component, vhx_remark, eds_remark, remark, created_by, created_date
                FROM eds
                WHERE component LIKE ?
                ORDER BY created_date DESC
                """, ('%' + component_name + '%',))
                return cursor.fetchall()
            finally:
                conn.close()

    def get_images_by_rowid(self, row_id):
        if self.db_type == "sqlite":
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            try:
                cursor.execute("""
                SELECT vhx_data, eds_data
                FROM eds WHERE rowid = ?
                """, (row_id,))
                result = cursor.fetchone()
                return result if result else (None, None)
            finally:
                conn.close()