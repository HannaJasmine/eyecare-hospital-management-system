import unittest

from app import app
from database import get_db_connection, get_summary_stats, init_db


class AppViewsTestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        self.client = app.test_client()

    def test_home_page_renders_layout_and_key_sections(self):
        response = self.client.get('/')

        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn('EyeCare Hospital', html)
        self.assertIn('Book Appointment', html)
        self.assertIn('Our Services', html)
        self.assertIn('Meet Our Specialists', html)
        self.assertIn('Why Choose EyeCare', html)

    def test_public_pages_render(self):
        for path, title in [
            ('/about', 'About EyeCare'),
            ('/services', 'Eye care services'),
            ('/doctors', 'Our Doctors'),
            ('/appointment', 'Book Appointment'),
            ('/contact', 'Contact Us'),
            ('/faq', 'Frequently Asked Questions'),
            ('/terms', 'Terms and Conditions'),
            ('/privacy', 'Privacy Policy'),
        ]:
            response = self.client.get(path)
            self.assertEqual(response.status_code, 200, msg=f'{path} did not load')
            self.assertIn(title, response.get_data(as_text=True))

    def test_admin_login_and_dashboard_pages(self):
        login_response = self.client.post('/admin/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)
        self.assertEqual(login_response.status_code, 200)
        self.assertIn('Admin Dashboard', login_response.get_data(as_text=True))

        for path, title in [
            ('/admin', 'Admin Dashboard'),
            ('/admin/patients', 'Patient Management'),
            ('/admin/doctors', 'Doctor Management'),
            ('/admin/appointments', 'Appointment Management'),
            ('/admin/billing', 'Billing Overview'),
            ('/admin/analytics', 'Data Analytics'),
        ]:
            response = self.client.get(path)
            self.assertEqual(response.status_code, 200, msg=f'{path} did not load')
            self.assertIn(title, response.get_data(as_text=True))

    def test_database_initializes_and_summary_stats_are_available(self):
        init_db()
        stats = get_summary_stats()
        self.assertIn('total_patients', stats)
        self.assertIn('total_doctors', stats)
        self.assertIn('today_appointments', stats)
        self.assertGreaterEqual(stats['total_patients'], 1)
        self.assertGreaterEqual(stats['total_doctors'], 1)

    def test_appointment_submission_persists_to_database(self):
        init_db()
        conn = get_db_connection()
        before = conn.execute("SELECT COUNT(*) FROM appointments WHERE patient_name = ?", ("Alice Gomez",)).fetchone()[0]
        conn.close()

        response = self.client.post('/appointment', data={
            'name': 'Alice Gomez',
            'email': 'alice@example.com',
            'phone': '+1 555 222 1111',
            'service': 'General Eye Examination',
            'doctor': 'Dr. Olivia Carter',
            'date': '2026-10-20',
            'message': 'New patient visit',
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn('Alice Gomez', response.get_data(as_text=True))
        self.assertIn('General Eye Examination', response.get_data(as_text=True))

        conn = get_db_connection()
        after = conn.execute("SELECT COUNT(*) FROM appointments WHERE patient_name = ?", ("Alice Gomez",)).fetchone()[0]
        conn.close()
        self.assertEqual(after, before + 1)

    def test_admin_can_update_appointment_status_and_add_doctor(self):
        init_db()
        self.client.post('/admin/login', data={'username': 'admin', 'password': 'admin123'})

        conn = get_db_connection()
        appointment_id = conn.execute("SELECT id FROM appointments ORDER BY id LIMIT 1").fetchone()[0]
        conn.close()

        update_response = self.client.post(
            f'/admin/appointments/{appointment_id}/update',
            data={'status': 'confirmed'},
            follow_redirects=True,
        )
        self.assertEqual(update_response.status_code, 200)

        conn = get_db_connection()
        status = conn.execute("SELECT status FROM appointments WHERE id = ?", (appointment_id,)).fetchone()[0]
        conn.close()
        self.assertEqual(status, 'confirmed')

        add_response = self.client.post(
            '/admin/doctors/add',
            data={
                'name': 'Dr. Anne Reed',
                'specialization': 'Retina',
                'schedule': 'Mon-Wed 09:00-15:00',
                'is_active': '1',
            },
            follow_redirects=True,
        )
        self.assertEqual(add_response.status_code, 200)

        conn = get_db_connection()
        doctor_exists = conn.execute(
            "SELECT COUNT(*) FROM doctors WHERE name = ? AND specialization = ?",
            ('Dr. Anne Reed', 'Retina'),
        ).fetchone()[0]
        conn.close()
        self.assertGreaterEqual(doctor_exists, 1)

    def test_admin_can_update_patient_and_bill_status(self):
        init_db()
        self.client.post('/admin/login', data={'username': 'admin', 'password': 'admin123'})

        conn = get_db_connection()
        patient_id = conn.execute("SELECT id FROM patients ORDER BY id LIMIT 1").fetchone()[0]
        bill_id = conn.execute("SELECT id FROM bills ORDER BY id LIMIT 1").fetchone()[0]
        conn.close()

        patient_response = self.client.post(
            f'/admin/patients/{patient_id}/update',
            data={
                'name': 'Emma Johnson Updated',
                'email': 'emma.updated@example.com',
                'phone': '+1 555 000 9999',
            },
            follow_redirects=True,
        )
        self.assertEqual(patient_response.status_code, 200)

        conn = get_db_connection()
        patient_name = conn.execute("SELECT name FROM patients WHERE id = ?", (patient_id,)).fetchone()[0]
        conn.close()
        self.assertEqual(patient_name, 'Emma Johnson Updated')

        bill_response = self.client.post(
            f'/admin/billing/{bill_id}/update',
            data={'payment_status': 'paid'},
            follow_redirects=True,
        )
        self.assertEqual(bill_response.status_code, 200)

        conn = get_db_connection()
        bill_status = conn.execute("SELECT payment_status FROM bills WHERE id = ?", (bill_id,)).fetchone()[0]
        conn.close()
        self.assertEqual(bill_status, 'paid')


if __name__ == '__main__':
    unittest.main()
