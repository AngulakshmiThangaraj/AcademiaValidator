import sqlite3
import os

def get_db_path():
    custom_path = os.environ.get("DATABASE_PATH")
    if custom_path:
        return custom_path
    
    default_dir = os.path.dirname(__file__)
    # Check if local dir is writable
    if os.access(default_dir, os.W_OK):
        return os.path.join(default_dir, "sih_certificates.db")
    
    # Fallback to system temp directory for serverless cloud environments
    import tempfile
    return os.path.join(tempfile.gettempdir(), "sih_certificates.db")

def get_db_connection():
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Table for Genuine Registered Certificates
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS registered_certificates (
        cert_id TEXT PRIMARY KEY,
        student_name TEXT NOT NULL,
        reg_no TEXT NOT NULL,
        institution TEXT NOT NULL,
        course TEXT NOT NULL,
        cgpa REAL NOT NULL,
        issue_date TEXT NOT NULL,
        sha256_hash TEXT NOT NULL,
        qr_signature TEXT,
        registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Table for Verification Audit Logs
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS verification_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cert_id TEXT,
        filename TEXT,
        authenticity_score REAL,
        status TEXT,
        ai_score REAL,
        ocr_consistency REAL,
        qr_validity REAL,
        ela_score REAL,
        hash_matched INTEGER,
        suspicious_regions_count INTEGER,
        verified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Seed initial test genuine certificates
    seed_records = [
        (
            "CERT-2025-1001",
            "Rohan Verma",
            "3122211001",
            "NATIONAL INSTITUTE OF TECHNOLOGY, TIRUCHIRAPPALLI",
            "BACHELOR OF TECHNOLOGY IN COMPUTER SCIENCE & ENGINEERING",
            8.75,
            "15-05-2024",
            "a8f5f167f44f4964e6c998dee827110c"
        ),
        (
            "CERT-2025-1002",
            "Priya Nair",
            "3122211002",
            "ANNA UNIVERSITY, CHENNAI",
            "BACHELOR OF TECHNOLOGY IN ELECTRONICS & COMMUNICATION",
            9.12,
            "18-05-2024",
            "c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8"
        ),
        (
            "CERT-2025-1003",
            "Arjun Iyer",
            "3122211003",
            "INDIAN INSTITUTE OF TECHNOLOGY, MADRAS",
            "BACHELOR OF TECHNOLOGY IN MECHANICAL ENGINEERING",
            8.40,
            "20-05-2024",
            "b1b2b3b4b5b6b7b8b9b0a1a2a3a4a5a6"
        )
    ]

    for record in seed_records:
        cursor.execute("""
        INSERT OR IGNORE INTO registered_certificates 
        (cert_id, student_name, reg_no, institution, course, cgpa, issue_date, sha256_hash)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, record)

    conn.commit()
    conn.close()
    print("Database initialized & seeded successfully!")

def get_certificate_by_id(cert_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM registered_certificates WHERE cert_id = ?", (cert_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def get_certificate_by_reg_no(reg_no):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM registered_certificates WHERE reg_no = ?", (reg_no,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def register_certificate(cert_id, student_name, reg_no, institution, course, cgpa, issue_date, sha256_hash, qr_signature=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT OR REPLACE INTO registered_certificates
    (cert_id, student_name, reg_no, institution, course, cgpa, issue_date, sha256_hash, qr_signature)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (cert_id, student_name, reg_no, institution, course, cgpa, issue_date, sha256_hash, qr_signature))
    conn.commit()
    conn.close()

def log_verification(cert_id, filename, score, status, ai_score, ocr_consistency, qr_validity, ela_score, hash_matched, suspicious_count):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO verification_logs 
    (cert_id, filename, authenticity_score, status, ai_score, ocr_consistency, qr_validity, ela_score, hash_matched, suspicious_regions_count)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (cert_id, filename, score, status, ai_score, ocr_consistency, qr_validity, ela_score, 1 if hash_matched else 0, suspicious_count))
    conn.commit()
    conn.close()

def get_recent_logs(limit=20):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM verification_logs ORDER BY verified_at DESC LIMIT ?", (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

if __name__ == "__main__":
    init_db()
