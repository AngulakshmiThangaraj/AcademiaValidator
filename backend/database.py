import sqlite3
import os
import hashlib

def get_db_path():
    custom_path = os.environ.get("DATABASE_PATH")
    if custom_path:
        return custom_path
    
    default_dir = os.path.dirname(__file__)
    if os.access(default_dir, os.W_OK):
        return os.path.join(default_dir, "sih_certificates.db")
    
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

    # 1. Table for Genuine Registered Higher Ed Certificates
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

    # 2. Table for Tamil Nadu State Board SSLC / HSC Marksheets
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tn_sslc_marksheets (
        certificate_id TEXT PRIMARY KEY,
        register_no TEXT NOT NULL,
        student_name TEXT NOT NULL,
        dob TEXT NOT NULL,
        father_name TEXT,
        mother_name TEXT,
        institution TEXT NOT NULL,
        course TEXT NOT NULL,
        total_marks INTEGER NOT NULL,
        result TEXT NOT NULL,
        passing_year TEXT NOT NULL,
        qr_payload_hash TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tn_cert_id ON tn_sslc_marksheets(certificate_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tn_reg_no ON tn_sslc_marksheets(register_no);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tn_name ON tn_sslc_marksheets(student_name);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tn_dob ON tn_sslc_marksheets(dob);")

    # Audit Logs
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

    # Seed initial higher ed test genuine certificates
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
        )
    ]

    for record in seed_records:
        cursor.execute("""
        INSERT OR REPLACE INTO registered_certificates 
        (cert_id, student_name, reg_no, institution, course, cgpa, issue_date, sha256_hash)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, record)

    # Seed SSLC Marksheet Record
    qr_payload = "TNSSLC|88880001|77770001|ANGULAKSHMI T|APR 2023"
    qr_hash = hashlib.sha256(qr_payload.encode('utf-8')).hexdigest()

    tn_seed_records = [
        (
            "88880001",
            "77770001",
            "ANGULAKSHMI T",
            "07/07/2007",
            "THANGARAJ A",
            "CHITHRA T",
            "GOVT HIGHER SECONDARY SCHOOL",
            "SSLC",
            451,
            "PASS",
            "APR 2023",
            qr_hash
        )
    ]

    for tn_record in tn_seed_records:
        cursor.execute("""
        INSERT OR REPLACE INTO tn_sslc_marksheets
        (certificate_id, register_no, student_name, dob, father_name, mother_name, institution, course, total_marks, result, passing_year, qr_payload_hash)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, tn_record)

    conn.commit()
    conn.close()

def get_tn_marksheet_by_id(cert_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tn_sslc_marksheets WHERE certificate_id = ?", (str(cert_id).strip(),))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def get_tn_marksheet_by_reg_no(reg_no):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tn_sslc_marksheets WHERE register_no = ?", (str(reg_no).strip(),))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def search_tn_marksheet(cert_id=None, reg_no=None, student_name=None, dob=None):
    """Finds best matching registry record based on available search keys."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if cert_id:
        cursor.execute("SELECT * FROM tn_sslc_marksheets WHERE certificate_id = ?", (str(cert_id).strip(),))
        row = cursor.fetchone()
        if row:
            conn.close()
            return dict(row)

    if reg_no:
        cursor.execute("SELECT * FROM tn_sslc_marksheets WHERE register_no = ?", (str(reg_no).strip(),))
        row = cursor.fetchone()
        if row:
            conn.close()
            return dict(row)

    if student_name and dob:
        clean_name = f"%{str(student_name).strip()}%"
        cursor.execute("SELECT * FROM tn_sslc_marksheets WHERE student_name LIKE ? AND dob = ?", (clean_name, str(dob).strip()))
        row = cursor.fetchone()
        if row:
            conn.close()
            return dict(row)

    conn.close()
    return None

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

def get_db_stats():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM verification_logs")
    total_scans = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM verification_logs WHERE status = 'VERIFIED'")
    verified_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM verification_logs WHERE status IN ('PARTIALLY_VERIFIED', 'REVIEW_REQUIRED', 'SUSPICIOUS')")
    warning_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM verification_logs WHERE status = 'INVALID'")
    failed_count = cursor.fetchone()[0]
    conn.close()
    return {
        "total_scans": total_scans,
        "verified_count": verified_count,
        "warning_count": warning_count,
        "failed_count": failed_count
    }

if __name__ == "__main__":
    init_db()
