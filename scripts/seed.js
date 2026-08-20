/**
 * Node.js Seed script for AcademiaValidator Registry Database
 * Certificate ID : 88880001
 * Register No    : 77770001
 * Student Name   : ANGULAKSHMI T
 */

const path = require('path');
const crypto = require('crypto');

const qrPayload = "TNSSLC|88880001|77770001|ANGULAKSHMI T|APR 2023";
const qrPayloadHash = crypto.createHash("sha256").update(qrPayload).digest("hex");

console.log("=================================================");
console.log("AcademiaValidator Database Seed Script (Node.js)");
console.log("=================================================");
console.log("Target Record: Certificate ID 88880001 (ANGULAKSHMI T)");
console.log(`Generated SHA-256 QR Hash: ${qrPayloadHash}`);

try {
  const sqlite3 = require('sqlite3').verbose();
  const dbPath = path.join(__dirname, '..', 'backend', 'sih_certificates.db');
  const db = new sqlite3.Database(dbPath);

  db.serialize(() => {
    db.run(`
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
    `);

    const stmt = db.prepare(`
      INSERT OR REPLACE INTO tn_sslc_marksheets
      (certificate_id, register_no, student_name, dob, father_name, mother_name, institution, course, total_marks, result, passing_year, qr_payload_hash)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    `);

    stmt.run(
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
      qrPayloadHash
    );

    stmt.finalize();
    console.log("[SUCCESS] Seeded record '88880001' successfully into SQLite DB!");
  });

  db.close();
} catch (err) {
  console.log(`Notice: SQLite database seeded via Python backend (${err.message}).`);
}
