from functools import wraps

import pandas as pd
import plotly.express as px
from flask import Flask, redirect, render_template, request, session, url_for

from database import (
    add_doctor,
    get_analytics_data,
    get_appointments,
    get_billing_summary,
    get_bills,
    get_doctors,
    get_latest_patients,
    get_summary_stats,
    get_patient_by_id,
    init_db,
    save_appointment,
    update_appointment_status,
    update_bill_status,
    update_patient,
    verify_admin_credentials,
)

app = Flask(__name__)
app.secret_key = "eyecare-hospital-admin-secret"

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

# Ensure the SQLite database and sample records exist when the app starts.
init_db()


def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if not session.get("admin_logged_in"):
            return redirect(url_for("admin_login"))
        return view(*args, **kwargs)

    return wrapped_view


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/services")
def services():
    return render_template("services.html")


@app.route("/doctors")
def doctors():
    return render_template("doctors.html")


@app.route("/appointment", methods=["GET", "POST"])
def appointment():
    success = False
    if request.method == "POST":
        patient_name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        phone = request.form.get("phone", "").strip()
        service = request.form.get("service", "").strip()
        doctor = request.form.get("doctor", "").strip()
        appointment_date = request.form.get("date", "").strip()
        message = request.form.get("message", "").strip()

        if patient_name and service and doctor and appointment_date:
            save_appointment(patient_name, email, phone, service, doctor, appointment_date, message)
            success = True

        return render_template(
            "appointment.html",
            success=success,
            patient_name=patient_name,
            service=service,
        )
    return render_template("appointment.html", success=False)


@app.route("/contact")
def contact():
    return render_template("contact.html")


@app.route("/faq")
def faq():
    return render_template("faq.html")


@app.route("/terms")
def terms():
    return render_template("terms.html")


@app.route("/privacy")
def privacy():
    return render_template("privacy.html")


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if session.get("admin_logged_in"):
        return redirect(url_for("admin_dashboard"))

    error = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if verify_admin_credentials(username, password) or (
            username == ADMIN_USERNAME and password == ADMIN_PASSWORD
        ):
            session["admin_logged_in"] = True
            session["admin_user"] = username
            return redirect(url_for("admin_dashboard"))

        error = "Invalid username or password."

    return render_template("admin_login.html", error=error)


@app.route("/admin/logout")
def admin_logout():
    session.clear()
    return redirect(url_for("admin_login"))


@app.route("/admin")
@login_required
def admin_dashboard():
    stats = get_summary_stats()
    patients = get_latest_patients(limit=5)
    return render_template("admin.html", stats=stats, patients=patients)


@app.route("/admin/patients")
@login_required
def admin_patients():
    patients = get_latest_patients(limit=10)
    return render_template("patients.html", patients=patients)


@app.route("/admin/patients/<int:patient_id>/update", methods=["POST"])
@login_required
def update_patient_route(patient_id):
    patient = get_patient_by_id(patient_id)
    if patient is None:
        return redirect(url_for("admin_patients"))

    name = request.form.get("name", patient["name"]).strip()
    email = request.form.get("email", patient["email"]).strip()
    phone = request.form.get("phone", patient["phone"]).strip()
    update_patient(patient_id, name, email, phone)
    return redirect(url_for("admin_patients"))


@app.route("/admin/doctors")
@login_required
def admin_doctors():
    doctors = get_doctors(limit=20)
    return render_template("manage_doctors.html", doctors=doctors)


@app.route("/admin/doctors/add", methods=["POST"])
@login_required
def add_doctor_route():
    name = request.form.get("name", "").strip()
    specialization = request.form.get("specialization", "").strip()
    schedule = request.form.get("schedule", "").strip()
    if name and specialization:
        add_doctor(name, specialization, schedule)
    return redirect(url_for("admin_doctors"))


@app.route("/admin/appointments")
@login_required
def admin_appointments():
    appointments = get_appointments(limit=10)
    return render_template("manage_appointments.html", appointments=appointments)


@app.route("/admin/appointments/<int:appointment_id>/update", methods=["POST"])
@login_required
def update_appointment_route(appointment_id):
    status = request.form.get("status", "pending").strip()
    update_appointment_status(appointment_id, status)
    return redirect(url_for("admin_appointments"))


@app.route("/admin/billing")
@login_required
def admin_billing():
    summary = get_billing_summary()
    bills = get_bills(limit=20)
    return render_template("billing.html", summary=summary, bills=bills)


@app.route("/admin/billing/<int:bill_id>/update", methods=["POST"])
@login_required
def update_bill_route(bill_id):
    payment_status = request.form.get("payment_status", "pending").strip()
    update_bill_status(bill_id, payment_status)
    return redirect(url_for("admin_billing"))


@app.route("/admin/analytics")
@login_required
def admin_analytics():
    data = get_analytics_data()
    status_df = pd.DataFrame(data["status"])
    service_df = pd.DataFrame(data["services"])

    status_chart = ""
    service_chart = ""

    if not status_df.empty:
        status_fig = px.pie(
            status_df,
            values="count",
            names="status",
            title="Appointment status",
            color_discrete_sequence=["#0f5b9a", "#5aaada", "#1fa97a", "#f7b267"],
        )
        status_chart = status_fig.to_html(full_html=False, include_plotlyjs="cdn")

    if not service_df.empty:
        service_fig = px.bar(
            service_df,
            x="service",
            y="count",
            title="Most requested services",
            color="service",
            color_discrete_sequence=px.colors.qualitative.Set2,
        )
        service_fig.update_layout(xaxis_title="Service", yaxis_title="Appointments")
        service_chart = service_fig.to_html(full_html=False, include_plotlyjs="cdn")

    stats = get_summary_stats()
    return render_template(
        "analytics.html",
        stats=stats,
        status_chart=status_chart,
        service_chart=service_chart,
    )


if __name__ == "__main__":
    app.run(debug=True)