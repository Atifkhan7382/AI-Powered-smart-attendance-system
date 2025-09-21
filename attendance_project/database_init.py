import sqlite3
import os
import logging
from datetime import datetime
from pathlib import Path
import json
import shutil # Added for the backup function

class DatabaseInitializer:
    """
    Complete database initialization for Smart Attendance System
    This should be run FIRST before any other system operations
    """
    
    def __init__(self, database_path: str = "attendance.db", backup_path: str = "backups/"):
        self.database_path = database_path
        self.backup_path = Path(backup_path)
        self.backup_path.mkdir(exist_ok=True)
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('database_init.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def initialize_database(self):
        """
        Complete database initialization with all required tables
        This is the MAIN function to call for database setup
        """
        self.logger.info("Starting database initialization...")
        
        try:
            # Create database connection
             sqlite3.connect(self.database_path)
            cursor = conn.cursor()
            
            # Enable foreign key support
            cursor.execute("PRAGMA foreign_keys = ON")
            
            # Create all tables
            self._create_students_table(cursor)
            self._create_attendance_table(cursor)
            self._create_classes_table(cursor)
            self._create_system_logs_table(cursor)
            self._create_face_encodings_table(cursor)
            
            # Create indexes for performance
            self._create_indexes(cursor)
            
            # Create views for reporting
            self._create_views(cursor)
            
            # Insert default data
            self._insert_default_data(cursor)
            
            # Commit all changes
            conn.commit()
            
            # Verify database structure
            self._verify_database_structure(cursor)
            
            conn.close()
            
            self.logger.info("Database initialization completed successfully!")
            self._create_initialization_report()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Database initialization failed: {str(e)}")
            return False
    
    def _create_students_table(self, cursor):
        """Create students table with all necessary fields"""
        create_students_sql = """
        CREATE TABLE IF NOT EXISTS students (
            student_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT UNIQUE,
            phone TEXT,
            class_section TEXT,
            enrollment_date DATE DEFAULT (date('now')),
            status TEXT DEFAULT 'Active' CHECK(status IN ('Active', 'Inactive', 'Graduated')),
            photo_count INTEGER DEFAULT 0,
            last_encoding_update TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        cursor.execute(create_students_sql)
        self.logger.info("Students table created/verified")
    
    def _create_attendance_table(self, cursor):
        """Create attendance table with comprehensive tracking"""
        create_attendance_sql = """
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT NOT NULL,
            date DATE NOT NULL,
            time TIME NOT NULL,
            status TEXT DEFAULT 'Present' CHECK(status IN ('Present', 'Absent', 'Late', 'Excused')),
            confidence REAL DEFAULT 0.0,
            image_path TEXT,
            processed_by TEXT DEFAULT 'System',
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES students (student_id) ON DELETE CASCADE,
            UNIQUE(student_id, date)
        )
        """
        cursor.execute(create_attendance_sql)
        self.logger.info("Attendance table created/verified")
    
    def _create_classes_table(self, cursor):
        """Create classes table for organizing students"""
        create_classes_sql = """
        CREATE TABLE IF NOT EXISTS classes (
            class_id TEXT PRIMARY KEY,
            class_name TEXT NOT NULL,
            instructor TEXT,
            room_number TEXT,
            schedule_time TEXT,
            semester TEXT,
            year INTEGER DEFAULT (strftime('%Y', 'now')),
            max_students INTEGER DEFAULT 50,
            status TEXT DEFAULT 'Active' CHECK(status IN ('Active', 'Inactive', 'Completed')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        cursor.execute(create_classes_sql)
        self.logger.info("Classes table created/verified")
    
    def _create_system_logs_table(self, cursor):
        """Create system logs table for monitoring"""
        create_logs_sql = """
        CREATE TABLE IF NOT EXISTS system_logs (
            log_id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            level TEXT CHECK(level IN ('INFO', 'WARNING', 'ERROR', 'CRITICAL')),
            module TEXT,
            message TEXT,
            details TEXT,
            processing_time_ms INTEGER,
            images_processed INTEGER DEFAULT 0,
            students_recognized INTEGER DEFAULT 0,
            system_memory_mb REAL,
            cpu_usage_percent REAL
        )
        """
        cursor.execute(create_logs_sql)
        self.logger.info("System logs table created/verified")
    
    def _create_face_encodings_table(self, cursor):
        """Create face encodings metadata table"""
        create_encodings_sql = """
        CREATE TABLE IF NOT EXISTS face_encodings_meta (
            encoding_id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT NOT NULL,
            image_filename TEXT,
            encoding_quality REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active BOOLEAN DEFAULT 1,
            FOREIGN KEY (student_id) REFERENCES students (student_id) ON DELETE CASCADE
        )
        """
        cursor.execute(create_encodings_sql)
        self.logger.info("Face encodings metadata table created/verified")
    
    def _create_indexes(self, cursor):
        """Create performance indexes"""
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_attendance_student_date ON attendance(student_id, date)",
            "CREATE INDEX IF NOT EXISTS idx_attendance_date ON attendance(date)",
            "CREATE INDEX IF NOT EXISTS idx_attendance_status ON attendance(status)",
            "CREATE INDEX IF NOT EXISTS idx_students_class ON students(class_section)",
            "CREATE INDEX IF NOT EXISTS idx_students_status ON students(status)",
            "CREATE INDEX IF NOT EXISTS idx_logs_timestamp ON system_logs(timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_logs_level ON system_logs(level)",
            "CREATE INDEX IF NOT EXISTS idx_encodings_student ON face_encodings_meta(student_id)"
        ]
        
        for index_sql in indexes:
            cursor.execute(index_sql)
        
        self.logger.info("Performance indexes created")
    
    def _create_views(self, cursor):
        """Create database views for easy reporting"""
        
        # Daily attendance summary view
        daily_summary_view = """
        CREATE VIEW IF NOT EXISTS daily_attendance_summary AS
        SELECT 
            date,
            COUNT(*) as total_present,
            COUNT(CASE WHEN status = 'Present' THEN 1 END) as present_count,
            COUNT(CASE WHEN status = 'Late' THEN 1 END) as late_count,
            COUNT(CASE WHEN status = 'Excused' THEN 1 END) as excused_count,
            AVG(confidence) as avg_confidence,
            MIN(time) as first_arrival,
            MAX(time) as last_arrival
        FROM attendance 
        GROUP BY date
        ORDER BY date DESC
        """
        cursor.execute(daily_summary_view)
        
        # Student attendance statistics view
        student_stats_view = """
        CREATE VIEW IF NOT EXISTS student_attendance_stats AS
        SELECT 
            s.student_id,
            s.name,
            s.class_section,
            COUNT(a.id) as total_days_marked,
            COUNT(CASE WHEN a.status = 'Present' THEN 1 END) as present_days,
            COUNT(CASE WHEN a.status = 'Late' THEN 1 END) as late_days,
            COUNT(CASE WHEN a.status = 'Absent' THEN 1 END) as absent_days,
            ROUND(COUNT(CASE WHEN a.status = 'Present' THEN 1 END) * 100.0 / COUNT(a.id), 2) as attendance_percentage,
            AVG(a.confidence) as avg_recognition_confidence,
            MAX(a.date) as last_attendance_date
        FROM students s
        LEFT JOIN attendance a ON s.student_id = a.student_id
        WHERE s.status = 'Active'
        GROUP BY s.student_id, s.name, s.class_section
        """
        cursor.execute(student_stats_view)
        
        self.logger.info("Database views created")
    
    def _insert_default_data(self, cursor):
        """Insert default classes and system data"""
        
        # Insert default classes
        default_classes = [
            ("CS101", "Introduction to Computer Science", "Dr. Smith", "Room 101", "MWF 10:00-11:00", "Fall", 2024),
            ("CS201", "Data Structures", "Dr. Johnson", "Room 102", "TTh 14:00-15:30", "Fall", 2024),
            ("MATH101", "Calculus I", "Prof. Williams", "Room 201", "MWF 09:00-10:00", "Fall", 2024)
        ]
        
        insert_class_sql = """
        INSERT OR IGNORE INTO classes 
        (class_id, class_name, instructor, room_number, schedule_time, semester, year)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        
        cursor.executemany(insert_class_sql, default_classes)
        
        # Insert initial system log
        cursor.execute("""
        INSERT INTO system_logs (level, module, message, details)
        VALUES ('INFO', 'DatabaseInitializer', 'Database initialized successfully', 
                 'All tables, indexes, and views created')
        """)
        
        self.logger.info("Default data inserted")
    
    def _verify_database_structure(self, cursor):
        """Verify all tables and structures are created correctly"""
        
        # Check tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        expected_tables = ['students', 'attendance', 'classes', 'system_logs', 'face_encodings_meta']
        
        for table in expected_tables:
            if table in tables:
                # Get table info
                cursor.execute(f"PRAGMA table_info({table})")
                columns = cursor.fetchall()
                self.logger.info(f"Table '{table}' verified with {len(columns)} columns")
            else:
                raise Exception(f"Table '{table}' was not created successfully")
        
        # Check views exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='view'")
        views = [row[0] for row in cursor.fetchall()]
        self.logger.info(f"Created {len(views)} database views")
        
        # Check indexes exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
        indexes = [row[0] for row in cursor.fetchall()]
        self.logger.info(f"Created {len(indexes)} performance indexes")
    
    def _create_initialization_report(self):
        """Create a detailed initialization report"""
        
        # Connect to get dynamic counts
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(name) FROM sqlite_master WHERE type='table'")
        tables_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(name) FROM sqlite_master WHERE type='view'")
        views_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(name) FROM sqlite_master WHERE type='index'")
        indexes_count = cursor.fetchone()[0]
        
        conn.close()
        
        report = {
            "initialization_timestamp": datetime.now().isoformat(),
            "database_path": self.database_path,
            "database_size_mb": round(os.path.getsize(self.database_path) / (1024*1024), 2) if os.path.exists(self.database_path) else 0,
            "status": "SUCCESS",
            "tables_created": tables_count,
            "views_created": views_count,
            "indexes_created": indexes_count,
            "default_classes_added": 3
        }
        
        # Save report as JSON
        report_path = f"database_init_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        self.logger.info(f"Initialization report saved: {report_path}")
        
        # Print summary to console
        print("\n" + "="*50)
        print("DATABASE INITIALIZATION COMPLETE")
        print("="*50)
        print(f"Database file: {self.database_path}")
        print(f"Database size: {report['database_size_mb']} MB")
        print(f"Tables created: {report['tables_created']}")
        print(f"Views created: {report['views_created']}")
        print(f"Indexes created: {report['indexes_created']}")
        print(f"Report saved: {report_path}")
        print("="*50)
    
    def add_sample_students(self):
        """Add sample students for testing (optional)"""
        sample_students = [
            ("2024001", "John Doe", "john.doe@university.edu", "+1234567890", "CS101"),
            ("2024002", "Jane Smith", "jane.smith@university.edu", "+1234567891", "CS101"),
            ("2024003", "Alice Johnson", "alice.johnson@university.edu", "+1234567892", "CS201"),
            ("2024004", "Bob Wilson", "bob.wilson@university.edu", "+1234567893", "CS201"),
            ("2024005", "Charlie Brown", "charlie.brown@university.edu", "+1234567894", "MATH101")
        ]
        
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        insert_student_sql = """
        INSERT OR IGNORE INTO students (student_id, name, email, phone, class_section)
        VALUES (?, ?, ?, ?, ?)
        """
        
        cursor.executemany(insert_student_sql, sample_students)
        conn.commit()
        conn.close()
        
        self.logger.info(f"Added {len(sample_students)} sample students")
        print(f"Sample students added: {len(sample_students)}")
    
    def backup_database(self):
        """Create a backup of the initialized database"""
        if os.path.exists(self.database_path):
            backup_filename = f"attendance_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
            backup_full_path = self.backup_path / backup_filename
            
            shutil.copy2(self.database_path, backup_full_path)
            
            self.logger.info(f"Database backup created: {backup_full_path}")
            print(f"Backup created: {backup_full_path}")
        else:
            self.logger.warning("No database file found to backup")


# MAIN EXECUTION FUNCTION - Run this to initialize your database
def main():
    """
    Main function to initialize the attendance system database
    RUN THIS FIRST before using the attendance system
    """
    
    print("Smart Attendance System - Database Initialization")
    print("="*55)
    
    # Initialize the database
    db_initializer = DatabaseInitializer(
        database_path="attendance.db",  # Your database file location
        backup_path="backups/"            # Where backups will be stored
    )
    
    # Step 1: Initialize database structure
    success = db_initializer.initialize_database()
    
    if success:
        # Step 2: Add sample students (optional - for testing)
        response = input("\nAdd sample students for testing? (y/n): ").lower().strip()
        if response == 'y':
            db_initializer.add_sample_students()
        
        # Step 3: Create initial backup
        db_initializer.backup_database()
        
        print("\n✅ Database initialization completed successfully!")
        print("✅ You can now run the main attendance system.")
        print("\nNext steps:")
        print("1. Add student photos to 'student_database/' C://Users//atifk//Desktop//Attendence//attendance_project//student_database")
        print("2. Run the main attendance system")
        print("3. Place classroom photos in 'classroom_photos/' C://Users//atifk//Desktop//Attendence//attendance_project//classroom_photos//classroom_photo.jpg")
        
    else:
        print("\n❌ Database initialization failed!")
        print("Check the logs for details: database_init.log")


# Run this script directly to initialize the database
if __name__ == "__main__":
    main()