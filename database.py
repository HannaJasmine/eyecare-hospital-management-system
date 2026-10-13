import os
import sqlite3
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "hospital.db")


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'admin'
        );

        CREATE TABLE IF NOT EXISTS patients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT,
            phone TEXT,
            date_of_birth TEXT,
            created_at TEXT DEFAULT CURRENT_DATE
        );

        CREATE TABLE IF NOT EXISTS doctors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            specialization TEXT NOT NULL,
            schedule TEXT,
            is_active INTEGER NOT NULL DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS departments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT
        );

        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_name TEXT NOT NULL,
            doctor_name TEXT NOT NULL,
            service TEXT NOT NULL,
            appointment_date TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending'
        );

        CREATE TABLE IF NOT EXISTS bills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_number TEXT NOT NULL UNIQUE,
            patient_name TEXT NOT NULL,
            appointment_id INTEGER,
            amount REAL NOT NULL,
            payment_status TEXT NOT NULL DEFAULT 'pending',
            payment_date TEXT
        );
        """
    )
    seed_sample_data(conn)
    conn.commit()
    conn.close()


def seed_sample_data(conn):
    admin_exists = conn.execute(
        "SELECT 1 FROM admins WHERE username = ?",
        ("admin",),
    ).fetchone()

    if not admin_exists:
        conn.execute(
            "INSERT INTO admins (username, password, role) VALUES (?, ?, ?)",
            ("admin", "admin123", "superadmin"),
        )

    if conn.execute("SELECT COUNT(*) FROM patients").fetchone()[0] == 0:
        conn.executemany(
            "INSERT INTO patients (name, email, phone, date_of_birth, created_at) VALUES (?, ?, ?, ?, ?)",
            [
                ("Emma Johnson", "emma@example.com", "+1 555 300 1101", "1990-04-12", "2026-09-18"),
                ("Daniel Martin", "daniel@example.com", "+1 555 300 1102", "1984-07-08", "2026-09-20"),
                ("Sophia Lee", "sophia@example.com", "+1 555 300 1103", "1998-02-14", "2026-09-28"),
            ],
        )

    if conn.execute("SELECT COUNT(*) FROM doctors").fetchone()[0] == 0:
        conn.executemany(
            "INSERT INTO doctors (name, specialization, schedule, is_active) VALUES (?, ?, ?, ?)",
            [
                ("Dr. Olivia Carter", "Cornea & Refractive Surgery", "Mon-Fri 09:00-17:00", 1),
                ("Dr. James Holloway", "Retina & Vitreous", "Tue-Sat 10:00-18:00", 1),
                ("Dr. Priya Shah", "Pediatric Ophthalmology", "Mon-Fri 08:00-15:00", 1),
                ("Dr. William Ross", "Glaucoma & Anterior Segment", "Wed-Sun 09:30-17:30", 1),
            ],
        )

    if conn.execute("SELECT COUNT(*) FROM departments").fetchone()[0] == 0:
        conn.executemany(
            "INSERT INTO departments (name, description) VALUES (?, ?)",
            [
                ("General Ophthalmology", "Routine checking and primary care."),
                ("Retina", "Retinal disease assessment and treatment."),
                ("Pediatric Eye Care", "Vision services for children and adolescents."),
            ],
        )

    if conn.execute("SELECT COUNT(*) FROM appointments").fetchone()[0] == 0:
        today = datetime.now().strftime("%Y-%m-%d")
        conn.executemany(
            "INSERT INTO appointments (patient_name, doctor_name, service, appointment_date, status) VALUES (?, ?, ?, ?, ?)",
            [
                ("Emma Johnson", "Dr. Olivia Carter", "General Eye Examination", today, "confirmed"),
                ("Daniel Martin", "Dr. William Ross", "Glaucoma Assessment", today, "pending"),
                ("Sophia Lee", "Dr. Priya Shah", "Pediatric Ophthalmology", "2026-10-12", "completed"),
                ("Emma Johnson", "Dr. James Holloway", "Retinal & Diabetic Care", "2026-10-15", "confirmed"),
            ],
        )

    if conn.execute("SELECT COUNT(*) FROM bills").fetchone()[0] == 0:
        conn.executemany(
            "INSERT INTO bills (invoice_number, patient_name, appointment_id, amount, payment_status, payment_date) VALUES (?, ?, ?, ?, ?, ?)",
            [
                ("INV-1001", "Emma Johnson", 1, 320.00, "paid", "2026-10-08"),
                ("INV-1002", "Daniel Martin", 2, 540.00, "pending", None),
                ("INV-1003", "Sophia Lee", 3, 410.00, "paid", "2026-10-06"),
            ],
        )


def get_summary_stats():
    conn = get_db_connection()
    stats = {
        "total_patients": conn.execute("SELECT COUNT(*) AS count FROM patients").fetchone()["count"],
        "total_doctors": conn.execute("SELECT COUNT(*) AS count FROM doctors").fetchone()["count"],
        "today_appointments": conn.execute(
            "SELECT COUNT(*) AS count FROM appointments WHERE appointment_date = date('now')"
        ).fetchone()["count"],
        "pending_appointments": conn.execute(
            "SELECT COUNT(*) AS count FROM appointments WHERE status = 'pending'"
        ).fetchone()["count"],
        "monthly_revenue": conn.execute(
            "SELECT COALESCE(SUM(amount), 0) AS total FROM bills WHERE payment_status = 'paid'"
        ).fetchone()["total"],
    }
    conn.close()
    return stats


def get_latest_patients(limit=5):
    conn = get_db_connection()
    rows = conn.execute(
        "SELECT id, name, email, phone, created_at FROM patients ORDER BY id DESC LIMIT ?",
        (limit,),
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_patient_by_id(patient_id):
    conn = get_db_connection()
    row = conn.execute(
        "SELECT id, name, email, phone, created_at FROM patients WHERE id = ?",
        (patient_id,),
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def update_patient(patient_id, name, email, phone):
    conn = get_db_connection()
    conn.execute(
        "UPDATE patients SET name = ?, email = ?, phone = ? WHERE id = ?",
        (name, email or None, phone or None, patient_id),
    )
    conn.commit()
    conn.close()


def get_appointments(limit=10):
    conn = get_db_connection()
    rows = conn.execute(
        "SELECT id, patient_name, doctor_name, service, appointment_date, status FROM appointments ORDER BY id DESC LIMIT ?",
        (limit,),
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_analytics_data():
    conn = get_db_connection()
    status_rows = conn.execute(
        "SELECT status, COUNT(*) AS count FROM appointments GROUP BY status ORDER BY count DESC"
    ).fetchall()
    service_rows = conn.execute(
        "SELECT service, COUNT(*) AS count FROM appointments GROUP BY service ORDER BY count DESC"
    ).fetchall()
    conn.close()
    return {
        "status": [dict(row) for row in status_rows],
        "services": [dict(row) for row in service_rows],
    }


def get_doctors(limit=20):
    conn = get_db_connection()
    rows = conn.execute(
        "SELECT id, name, specialization, schedule, is_active FROM doctors ORDER BY id DESC LIMIT ?",
        (limit,),
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def save_appointment(patient_name, email, phone, service, doctor_name, appointment_date, message=None):
    conn = get_db_connection()
    existing_patient = conn.execute(
        "SELECT id FROM patients WHERE email = ? OR name = ?",
        (email or "", patient_name),
    ).fetchone()

    if existing_patient is None:
        conn.execute(
            "INSERT INTO patients (name, email, phone, date_of_birth, created_at) VALUES (?, ?, ?, ?, date('now'))",
            (patient_name, email or None, phone or None, None),
        )

    conn.execute(
        "INSERT INTO appointments (patient_name, doctor_name, service, appointment_date, status) VALUES (?, ?, ?, ?, 'pending')",
        (patient_name, doctor_name, service, appointment_date),
    )
    conn.commit()
    conn.close()


def update_appointment_status(appointment_id, status):
    conn = get_db_connection()
    conn.execute(
        "UPDATE appointments SET status = ? WHERE id = ?",
        (status, appointment_id),
    )
    conn.commit()
    conn.close()


def add_doctor(name, specialization, schedule, is_active=True):
    conn = get_db_connection()
    conn.execute(
        "INSERT INTO doctors (name, specialization, schedule, is_active) VALUES (?, ?, ?, ?)",
        (name, specialization, schedule, 1 if is_active else 0),
    )
    conn.commit()
    conn.close()


def get_billing_summary():
    conn = get_db_connection()
    summary = {
        "monthly_revenue": conn.execute(
            "SELECT COALESCE(SUM(amount), 0) AS total FROM bills WHERE payment_status = 'paid'"
        ).fetchone()["total"],
        "outstanding": conn.execute(
            "SELECT COALESCE(SUM(amount), 0) AS total FROM bills WHERE payment_status != 'paid'"
        ).fetchone()["total"],
        "paid_invoices": conn.execute(
            "SELECT COUNT(*) AS count FROM bills WHERE payment_status = 'paid'"
        ).fetchone()["count"],
        "pending_count": conn.execute(
            "SELECT COUNT(*) AS count FROM bills WHERE payment_status = 'pending'"
        ).fetchone()["count"],
        "total_invoices": conn.execute("SELECT COUNT(*) AS count FROM bills").fetchone()["count"],
    }
    conn.close()
    summary["paid_percentage"] = round((summary["paid_invoices"] / summary["total_invoices"]) * 100, 1) if summary["total_invoices"] else 0
    return summary


def get_bills(limit=20):
    conn = get_db_connection()
    rows = conn.execute(
        "SELECT id, invoice_number, patient_name, appointment_id, amount, payment_status, payment_date FROM bills ORDER BY id DESC LIMIT ?",
        (limit,),
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def update_bill_status(bill_id, payment_status):
    conn = get_db_connection()
    conn.execute(
        "UPDATE bills SET payment_status = ?, payment_date = COALESCE(payment_date, date('now')) WHERE id = ?",
        (payment_status, bill_id),
    )
    conn.commit()
    conn.close()


def verify_admin_credentials(username, password):
    conn = get_db_connection()
    row = conn.execute(
        "SELECT password FROM admins WHERE username = ?",
        (username,),
    ).fetchone()
    conn.close()
    if row is None:
        return False
    return row["password"] == password
