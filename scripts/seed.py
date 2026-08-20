import sys
import os
import sqlite3
import hashlib

backend_dir = os.path.join(os.path.dirname(__file__), "..", "backend")
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from database import init_db, get_db_connection

def run_seed():
    print("=================================================")
    print("AcademiaValidator Database Seed Script")
    print("=================================================")

    init_db()

    qr_payload = "TNSSLC|24353750|53959247|ANGULAKSHMI T|APR 2023"
    qr_hash = hashlib.sha256(qr_payload.encode('utf-8')).hexdigest()

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
    INSERT OR REPLACE INTO tn_sslc_marksheets
    (certificate_id, register_no, student_name, dob, father_name, mother_name, institution, course, total_marks, result, passing_year, qr_payload_hash)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        "24353750",
        "53959247",
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
    ))

    conn.commit()
    conn.close()

    print("[SUCCESS] Successfully seeded record '24353750' (ANGULAKSHMI T) into registry database!")
    print(f"SHA-256 QR Payload Hash: {qr_hash}")

if __name__ == '__main__':
    run_seed()
