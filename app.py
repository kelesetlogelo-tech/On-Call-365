import io
import os
from datetime import date, datetime, timedelta

from flask import Flask, abort, flash, make_response, redirect, render_template, request, url_for
from flask_login import LoginManager, current_user, login_required, login_user, logout_user
from flask_mail import Mail, Message
from flask_wtf.csrf import CSRFProtect
from weasyprint import HTML

from config import Config
from forms import AppointmentForm, DoctorForm, InvoiceForm, LoginForm, PatientForm, RegisterForm
from models import Appointment, Doctor, Invoice, InvoiceItem, Patient, User, db

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)

csrf = CSRFProtect(app)

mail = Mail(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"
login_manager.login_message_category = "info"


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


with app.app_context():
    os.makedirs(os.path.join(app.instance_path), exist_ok=True)
    db.create_all()


@app.context_processor
def inject_now():
    return {"now": datetime.utcnow}


# ──────────────────────────────────────────────
# Auth routes
# ──────────────────────────────────────────────
@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            flash("Welcome back!", "success")
            next_page = request.args.get("next")
            return redirect(next_page or url_for("dashboard"))
        flash("Invalid username or password.", "danger")
    return render_template("login.html", form=form)


@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    form = RegisterForm()
    if form.validate_on_submit():
        if User.query.filter_by(username=form.username.data).first():
            flash("Username already exists.", "danger")
            return render_template("register.html", form=form)
        if User.query.filter_by(email=form.email.data).first():
            flash("Email already registered.", "danger")
            return render_template("register.html", form=form)
        user = User(username=form.username.data, email=form.email.data, full_name=form.full_name.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash("Account created! Please log in.", "success")
        return redirect(url_for("login"))
    return render_template("register.html", form=form)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("login"))


# ──────────────────────────────────────────────
# Dashboard
# ──────────────────────────────────────────────
@app.route("/")
@login_required
def dashboard():
    today = date.today()
    total_patients = Patient.query.count()
    total_doctors = Doctor.query.filter_by(is_active=True).count()
    todays_appointments = Appointment.query.filter_by(appointment_date=today).count()
    total_appointments = Appointment.query.count()

    upcoming = (
        Appointment.query.filter(Appointment.appointment_date >= today, Appointment.status.in_(["Scheduled", "Confirmed"]))
        .order_by(Appointment.appointment_date, Appointment.appointment_time)
        .limit(5)
        .all()
    )

    recent_patients = Patient.query.order_by(Patient.created_at.desc()).limit(5).all()

    week_start = today - timedelta(days=today.weekday())
    weekly_stats = []
    for i in range(7):
        d = week_start + timedelta(days=i)
        count = Appointment.query.filter_by(appointment_date=d).count()
        weekly_stats.append({"day": d.strftime("%a"), "date": d.strftime("%d %b"), "count": count})

    status_counts = {}
    for status in ["Scheduled", "Confirmed", "Completed", "Cancelled", "No Show"]:
        status_counts[status] = Appointment.query.filter_by(status=status).count()

    return render_template(
        "dashboard.html",
        total_patients=total_patients,
        total_doctors=total_doctors,
        todays_appointments=todays_appointments,
        total_appointments=total_appointments,
        upcoming=upcoming,
        recent_patients=recent_patients,
        weekly_stats=weekly_stats,
        status_counts=status_counts,
        today=today,
    )


# ──────────────────────────────────────────────
# Patients
# ──────────────────────────────────────────────
@app.route("/patients")
@login_required
def patient_list():
    search = request.args.get("search", "")
    if search:
        patients = Patient.query.filter(
            (Patient.first_name.ilike(f"%{search}%"))
            | (Patient.last_name.ilike(f"%{search}%"))
            | (Patient.phone.ilike(f"%{search}%"))
            | (Patient.file_number.ilike(f"%{search}%"))
        ).order_by(Patient.last_name).all()
    else:
        patients = Patient.query.order_by(Patient.last_name).all()
    return render_template("patients/list.html", patients=patients, search=search)


@app.route("/patients/add", methods=["GET", "POST"])
@login_required
def patient_add():
    form = PatientForm()
    next_file_number = Patient.generate_next_file_number()
    if form.validate_on_submit():
        patient = Patient(
            file_number=Patient.generate_next_file_number(),
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            date_of_birth=form.date_of_birth.data,
            gender=form.gender.data,
            phone=form.phone.data,
            email=form.email.data,
            address=form.address.data,
            payment_type=form.payment_type.data,
            medical_aid_name=form.medical_aid_name.data if form.payment_type.data == "Medical Aid" else None,
            medical_aid_number=form.medical_aid_number.data if form.payment_type.data == "Medical Aid" else None,
            emergency_contact_name=form.emergency_contact_name.data,
            emergency_contact_phone=form.emergency_contact_phone.data,
            notes=form.notes.data,
        )
        db.session.add(patient)
        db.session.commit()
        flash(f"Patient {patient.full_name} (File: {patient.file_number}) added successfully.", "success")
        return redirect(url_for("patient_view", patient_id=patient.id))
    return render_template("patients/add.html", form=form, next_file_number=next_file_number)


@app.route("/patients/<int:patient_id>")
@login_required
def patient_view(patient_id):
    patient = db.session.get(Patient, patient_id) or abort(404)
    appointments = (
        Appointment.query.filter_by(patient_id=patient_id)
        .order_by(Appointment.appointment_date.desc())
        .all()
    )
    return render_template("patients/view.html", patient=patient, appointments=appointments)


@app.route("/patients/<int:patient_id>/edit", methods=["GET", "POST"])
@login_required
def patient_edit(patient_id):
    patient = db.session.get(Patient, patient_id) or abort(404)
    form = PatientForm(obj=patient)
    if form.validate_on_submit():
        form.populate_obj(patient)
        if patient.payment_type == "Cash":
            patient.medical_aid_name = None
            patient.medical_aid_number = None
        db.session.commit()
        flash(f"Patient {patient.full_name} updated.", "success")
        return redirect(url_for("patient_view", patient_id=patient.id))
    return render_template("patients/edit.html", form=form, patient=patient)


@app.route("/patients/<int:patient_id>/delete", methods=["POST"])
@login_required
def patient_delete(patient_id):
    patient = db.session.get(Patient, patient_id) or abort(404)
    name = patient.full_name
    db.session.delete(patient)
    db.session.commit()
    flash(f"Patient {name} deleted.", "success")
    return redirect(url_for("patient_list"))


# ──────────────────────────────────────────────
# Doctors
# ──────────────────────────────────────────────
@app.route("/doctors")
@login_required
def doctor_list():
    doctors = Doctor.query.order_by(Doctor.last_name).all()
    return render_template("doctors/list.html", doctors=doctors)


@app.route("/doctors/add", methods=["GET", "POST"])
@login_required
def doctor_add():
    form = DoctorForm()
    if form.validate_on_submit():
        doctor = Doctor(
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            specialization=form.specialization.data,
            phone=form.phone.data,
            email=form.email.data,
            license_number=form.license_number.data,
        )
        db.session.add(doctor)
        db.session.commit()
        flash(f"{doctor.full_name} added successfully.", "success")
        return redirect(url_for("doctor_list"))
    return render_template("doctors/add.html", form=form)


@app.route("/doctors/<int:doctor_id>/edit", methods=["GET", "POST"])
@login_required
def doctor_edit(doctor_id):
    doctor = db.session.get(Doctor, doctor_id) or abort(404)
    form = DoctorForm(obj=doctor)
    if form.validate_on_submit():
        form.populate_obj(doctor)
        db.session.commit()
        flash(f"{doctor.full_name} updated.", "success")
        return redirect(url_for("doctor_list"))
    return render_template("doctors/edit.html", form=form, doctor=doctor)


@app.route("/doctors/<int:doctor_id>/delete", methods=["POST"])
@login_required
def doctor_delete(doctor_id):
    doctor = db.session.get(Doctor, doctor_id) or abort(404)
    name = doctor.full_name
    db.session.delete(doctor)
    db.session.commit()
    flash(f"{name} removed.", "success")
    return redirect(url_for("doctor_list"))


@app.route("/doctors/<int:doctor_id>/toggle", methods=["POST"])
@login_required
def doctor_toggle(doctor_id):
    doctor = db.session.get(Doctor, doctor_id) or abort(404)
    doctor.is_active = not doctor.is_active
    db.session.commit()
    status = "activated" if doctor.is_active else "deactivated"
    flash(f"{doctor.full_name} {status}.", "success")
    return redirect(url_for("doctor_list"))


# ──────────────────────────────────────────────
# Appointments
# ──────────────────────────────────────────────
@app.route("/appointments")
@login_required
def appointment_list():
    status_filter = request.args.get("status", "")
    date_filter = request.args.get("date", "")
    query = Appointment.query
    if status_filter:
        query = query.filter_by(status=status_filter)
    if date_filter:
        try:
            filter_date = datetime.strptime(date_filter, "%Y-%m-%d").date()
            query = query.filter_by(appointment_date=filter_date)
        except ValueError:
            pass
    appointments = query.order_by(Appointment.appointment_date.desc(), Appointment.appointment_time.desc()).all()
    return render_template("appointments/list.html", appointments=appointments, status_filter=status_filter, date_filter=date_filter)


@app.route("/appointments/add", methods=["GET", "POST"])
@login_required
def appointment_add():
    form = AppointmentForm()
    form.patient_id.choices = [(p.id, p.full_name) for p in Patient.query.order_by(Patient.last_name).all()]
    form.doctor_id.choices = [(d.id, d.full_name) for d in Doctor.query.filter_by(is_active=True).order_by(Doctor.last_name).all()]
    if form.validate_on_submit():
        appt = Appointment(
            patient_id=form.patient_id.data,
            doctor_id=form.doctor_id.data,
            appointment_date=form.appointment_date.data,
            appointment_time=form.appointment_time.data,
            duration_minutes=form.duration_minutes.data,
            reason=form.reason.data,
            status=form.status.data,
            notes=form.notes.data,
        )
        db.session.add(appt)
        db.session.commit()
        flash("Appointment scheduled.", "success")
        return redirect(url_for("appointment_list"))
    return render_template("appointments/add.html", form=form)


@app.route("/appointments/<int:appt_id>/edit", methods=["GET", "POST"])
@login_required
def appointment_edit(appt_id):
    appt = db.session.get(Appointment, appt_id) or abort(404)
    form = AppointmentForm(obj=appt)
    form.patient_id.choices = [(p.id, p.full_name) for p in Patient.query.order_by(Patient.last_name).all()]
    form.doctor_id.choices = [(d.id, d.full_name) for d in Doctor.query.filter_by(is_active=True).order_by(Doctor.last_name).all()]
    if form.validate_on_submit():
        form.populate_obj(appt)
        db.session.commit()
        flash("Appointment updated.", "success")
        return redirect(url_for("appointment_list"))
    return render_template("appointments/edit.html", form=form, appt=appt)


@app.route("/appointments/<int:appt_id>/delete", methods=["POST"])
@login_required
def appointment_delete(appt_id):
    appt = db.session.get(Appointment, appt_id) or abort(404)
    db.session.delete(appt)
    db.session.commit()
    flash("Appointment deleted.", "success")
    return redirect(url_for("appointment_list"))


@app.route("/appointments/<int:appt_id>/status/<status>", methods=["POST"])
@login_required
def appointment_status(appt_id, status):
    appt = db.session.get(Appointment, appt_id) or abort(404)
    if status in ["Scheduled", "Confirmed", "In Progress", "Completed", "Cancelled", "No Show"]:
        appt.status = status
        db.session.commit()
        flash(f"Appointment status changed to {status}.", "success")
    return redirect(url_for("appointment_list"))


# ──────────────────────────────────────────────
# Accounts & Invoices
# ──────────────────────────────────────────────
@app.route("/accounts")
@login_required
def accounts_summary():
    today = date.today()
    period = request.args.get("period", "weekly")

    if period == "monthly":
        start_date = today.replace(day=1)
        if today.month == 12:
            end_date = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            end_date = today.replace(month=today.month + 1, day=1) - timedelta(days=1)
        period_label = today.strftime("%B %Y")
    else:
        start_date = today - timedelta(days=today.weekday())
        end_date = start_date + timedelta(days=6)
        period_label = f"{start_date.strftime('%d %b')} – {end_date.strftime('%d %b %Y')}"

    invoices = Invoice.query.filter(
        Invoice.invoice_date >= start_date,
        Invoice.invoice_date <= end_date,
    ).all()

    total_revenue = sum(inv.total for inv in invoices)
    cash_revenue = sum(inv.total for inv in invoices if inv.patient.payment_type == "Cash")
    medical_aid_revenue = total_revenue - cash_revenue

    paid_invoices = [inv for inv in invoices if inv.status == "Paid"]
    unpaid_invoices = [inv for inv in invoices if inv.status != "Paid"]
    total_paid = sum(inv.total for inv in paid_invoices)
    total_unpaid = sum(inv.total for inv in unpaid_invoices)

    return render_template(
        "accounts/summary.html",
        period=period,
        period_label=period_label,
        invoices=invoices,
        total_revenue=total_revenue,
        cash_revenue=cash_revenue,
        medical_aid_revenue=medical_aid_revenue,
        total_paid=total_paid,
        total_unpaid=total_unpaid,
        invoice_count=len(invoices),
    )


@app.route("/accounts/invoices")
@login_required
def invoice_list():
    status_filter = request.args.get("status", "")
    query = Invoice.query
    if status_filter:
        query = query.filter_by(status=status_filter)
    invoices = query.order_by(Invoice.invoice_date.desc()).all()
    return render_template("accounts/invoice_list.html", invoices=invoices, status_filter=status_filter)


@app.route("/accounts/invoices/create", methods=["GET", "POST"])
@login_required
def invoice_create():
    form = InvoiceForm()
    cash_patients = Patient.query.filter_by(payment_type="Cash").order_by(Patient.last_name).all()
    form.patient_id.choices = [(p.id, f"{p.full_name} ({p.file_number})") for p in cash_patients]

    if form.validate_on_submit():
        invoice = Invoice(
            invoice_number=Invoice.generate_next_invoice_number(),
            patient_id=form.patient_id.data,
            invoice_date=form.invoice_date.data,
            due_date=form.due_date.data,
            payment_method=form.payment_method.data,
            notes=form.notes.data,
        )
        db.session.add(invoice)
        db.session.flush()

        for item_form in form.items:
            if item_form.description.data:
                item = InvoiceItem(
                    invoice_id=invoice.id,
                    description=item_form.description.data,
                    quantity=item_form.quantity.data,
                    unit_price=float(item_form.unit_price.data),
                )
                db.session.add(item)

        db.session.commit()
        flash(f"Invoice {invoice.invoice_number} created successfully.", "success")
        return redirect(url_for("invoice_view", invoice_id=invoice.id))

    next_invoice_number = Invoice.generate_next_invoice_number()
    return render_template("accounts/invoice_create.html", form=form, next_invoice_number=next_invoice_number)


@app.route("/accounts/invoices/<int:invoice_id>")
@login_required
def invoice_view(invoice_id):
    invoice = db.session.get(Invoice, invoice_id) or abort(404)
    return render_template("accounts/invoice_view.html", invoice=invoice)


@app.route("/accounts/invoices/<int:invoice_id>/status/<status>", methods=["POST"])
@login_required
def invoice_status(invoice_id, status):
    invoice = db.session.get(Invoice, invoice_id) or abort(404)
    if status in ["Paid", "Unpaid", "Overdue", "Cancelled"]:
        invoice.status = status
        db.session.commit()
        flash(f"Invoice {invoice.invoice_number} marked as {status}.", "success")
    return redirect(url_for("invoice_view", invoice_id=invoice.id))


@app.route("/accounts/invoices/<int:invoice_id>/pdf")
@login_required
def invoice_pdf(invoice_id):
    invoice = db.session.get(Invoice, invoice_id) or abort(404)
    html_content = render_template("accounts/invoice_pdf.html", invoice=invoice)
    pdf = HTML(string=html_content).write_pdf()
    response = make_response(pdf)
    response.headers["Content-Type"] = "application/pdf"
    response.headers["Content-Disposition"] = f"inline; filename={invoice.invoice_number}.pdf"
    return response


@app.route("/accounts/invoices/<int:invoice_id>/email", methods=["POST"])
@login_required
def invoice_email(invoice_id):
    invoice = db.session.get(Invoice, invoice_id) or abort(404)
    patient = invoice.patient

    if not patient.email:
        flash("This patient does not have an email address on file.", "danger")
        return redirect(url_for("invoice_view", invoice_id=invoice.id))

    if not app.config.get("MAIL_SERVER"):
        flash("Email is not configured. Please set MAIL_SERVER, MAIL_USERNAME, and MAIL_PASSWORD in your environment.", "warning")
        return redirect(url_for("invoice_view", invoice_id=invoice.id))

    try:
        html_content = render_template("accounts/invoice_pdf.html", invoice=invoice)
        pdf = HTML(string=html_content).write_pdf()

        msg = Message(
            subject=f"Invoice {invoice.invoice_number} - MedPractice",
            sender=app.config.get("MAIL_DEFAULT_SENDER", "noreply@medpractice.com"),
            recipients=[patient.email],
        )
        msg.html = render_template("accounts/invoice_email.html", invoice=invoice, patient=patient)
        msg.attach(f"{invoice.invoice_number}.pdf", "application/pdf", pdf)
        mail.send(msg)
        flash(f"Invoice emailed to {patient.email}.", "success")
    except Exception as e:
        flash(f"Failed to send email: {str(e)}", "danger")

    return redirect(url_for("invoice_view", invoice_id=invoice.id))


@app.route("/accounts/invoices/<int:invoice_id>/delete", methods=["POST"])
@login_required
def invoice_delete(invoice_id):
    invoice = db.session.get(Invoice, invoice_id) or abort(404)
    inv_num = invoice.invoice_number
    db.session.delete(invoice)
    db.session.commit()
    flash(f"Invoice {inv_num} deleted.", "success")
    return redirect(url_for("invoice_list"))


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
