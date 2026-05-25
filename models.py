from datetime import datetime, date

from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash

db = SQLAlchemy()


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    full_name = db.Column(db.String(150), nullable=False)
    role = db.Column(db.String(20), default="staff")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Patient(db.Model):
    __tablename__ = "patients"

    FILE_NUMBER_PREFIX = "KMC"
    FILE_NUMBER_START = 26001

    id = db.Column(db.Integer, primary_key=True)
    file_number = db.Column(db.String(20), unique=True, nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    date_of_birth = db.Column(db.Date, nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(120))
    address = db.Column(db.Text)
    payment_type = db.Column(db.String(20), nullable=False, default="Medical Aid")
    medical_aid_name = db.Column(db.String(100))
    medical_aid_number = db.Column(db.String(50))
    emergency_contact_name = db.Column(db.String(150))
    emergency_contact_phone = db.Column(db.String(20))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    appointments = db.relationship("Appointment", backref="patient", lazy=True, cascade="all, delete-orphan")

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def age(self):
        today = date.today()
        return today.year - self.date_of_birth.year - (
            (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
        )

    @staticmethod
    def generate_next_file_number():
        last_patient = (
            Patient.query.order_by(Patient.id.desc()).first()
        )
        if last_patient and last_patient.file_number:
            numeric_part = int(last_patient.file_number[len(Patient.FILE_NUMBER_PREFIX):])
            next_number = numeric_part + 1
        else:
            next_number = Patient.FILE_NUMBER_START
        return f"{Patient.FILE_NUMBER_PREFIX}{next_number}"


class Doctor(db.Model):
    __tablename__ = "doctors"

    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    specialization = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    license_number = db.Column(db.String(50), unique=True, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    appointments = db.relationship("Appointment", backref="doctor", lazy=True)

    @property
    def full_name(self):
        return f"Dr. {self.first_name} {self.last_name}"


class Appointment(db.Model):
    __tablename__ = "appointments"

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey("patients.id"), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey("doctors.id"), nullable=False)
    appointment_date = db.Column(db.Date, nullable=False)
    appointment_time = db.Column(db.Time, nullable=False)
    duration_minutes = db.Column(db.Integer, default=30)
    reason = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default="Scheduled")
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Invoice(db.Model):
    __tablename__ = "invoices"

    INVOICE_PREFIX = "INV"
    INVOICE_START = 1001

    PAYMENT_METHODS = [
        ("EFT", "EFT"),
        ("CASH", "CASH"),
        ("PAYSHAP", "PAYSHAP"),
        ("CASHSEND", "CASHSEND"),
        ("EWALLET", "EWALLET"),
        ("CAPITECPAY", "CAPITECPAY"),
    ]

    id = db.Column(db.Integer, primary_key=True)
    invoice_number = db.Column(db.String(20), unique=True, nullable=False)
    patient_id = db.Column(db.Integer, db.ForeignKey("patients.id"), nullable=False)
    invoice_date = db.Column(db.Date, nullable=False, default=date.today)
    due_date = db.Column(db.Date)
    payment_method = db.Column(db.String(20), nullable=False, default="CASH")
    status = db.Column(db.String(20), nullable=False, default="Unpaid")
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    patient = db.relationship("Patient", backref=db.backref("invoices", lazy=True))
    items = db.relationship("InvoiceItem", backref="invoice", lazy=True, cascade="all, delete-orphan")

    @property
    def subtotal(self):
        return sum(item.total for item in self.items)

    @property
    def vat_amount(self):
        return round(self.subtotal * 0.15, 2)

    @property
    def total(self):
        return round(self.subtotal + self.vat_amount, 2)

    @staticmethod
    def generate_next_invoice_number():
        last_invoice = Invoice.query.order_by(Invoice.id.desc()).first()
        if last_invoice and last_invoice.invoice_number:
            numeric_part = int(last_invoice.invoice_number[len(Invoice.INVOICE_PREFIX):])
            next_number = numeric_part + 1
        else:
            next_number = Invoice.INVOICE_START
        return f"{Invoice.INVOICE_PREFIX}{next_number}"


class InvoiceItem(db.Model):
    __tablename__ = "invoice_items"

    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey("invoices.id"), nullable=False)
    description = db.Column(db.String(200), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    unit_price = db.Column(db.Float, nullable=False)

    @property
    def total(self):
        return round(self.quantity * self.unit_price, 2)
