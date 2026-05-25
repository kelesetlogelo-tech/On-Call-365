"""Populate the database with sample data for demonstration."""

import os
import sys
from datetime import date, time, timedelta

from app import app, db
from models import Appointment, Doctor, Invoice, InvoiceItem, Patient, User


def seed():
    with app.app_context():
        if User.query.first():
            print("Database already has data. Skipping seed.")
            return

        # Admin user
        admin = User(username="admin", email="admin@medpractice.com", full_name="Admin User", role="admin")
        admin.set_password("admin123")
        db.session.add(admin)

        # Doctors
        doctors = [
            Doctor(first_name="Sarah", last_name="Nkosi", specialization="General Practice", phone="082 111 2222", email="sarah.nkosi@medpractice.com", license_number="MP-10001"),
            Doctor(first_name="James", last_name="Van der Merwe", specialization="Cardiology", phone="083 333 4444", email="james.vdm@medpractice.com", license_number="MP-10002"),
            Doctor(first_name="Priya", last_name="Pillay", specialization="Pediatrics", phone="084 555 6666", email="priya.pillay@medpractice.com", license_number="MP-10003"),
        ]
        db.session.add_all(doctors)

        # Patients
        patients = [
            Patient(file_number="KMC26001", first_name="Thabo", last_name="Mokoena", date_of_birth=date(1985, 3, 15), gender="Male", phone="071 100 2000", email="thabo.m@email.com", address="12 Main Rd, Sandton", payment_type="Medical Aid", medical_aid_name="Discovery Health", medical_aid_number="DH-900001", emergency_contact_name="Lerato Mokoena", emergency_contact_phone="071 200 3000"),
            Patient(file_number="KMC26002", first_name="Anele", last_name="Dlamini", date_of_birth=date(1992, 7, 22), gender="Female", phone="072 300 4000", email="anele.d@email.com", address="45 Oak Ave, Rosebank", payment_type="Medical Aid", medical_aid_name="Bonitas", medical_aid_number="BN-800002"),
            Patient(file_number="KMC26003", first_name="Pieter", last_name="Botha", date_of_birth=date(1978, 11, 8), gender="Male", phone="073 500 6000", email="pieter.b@email.com", address="8 Church St, Pretoria", payment_type="Medical Aid", medical_aid_name="Momentum Health", medical_aid_number="MH-700003"),
            Patient(file_number="KMC26004", first_name="Fatima", last_name="Ismail", date_of_birth=date(2001, 1, 30), gender="Female", phone="074 700 8000", email="fatima.i@email.com", address="22 Lemon Rd, Durban", payment_type="Cash"),
            Patient(file_number="KMC26005", first_name="David", last_name="Mthembu", date_of_birth=date(1965, 5, 12), gender="Male", phone="075 900 1000", address="3 Hill St, Bloemfontein", payment_type="Medical Aid", medical_aid_name="Discovery Health", medical_aid_number="DH-600005", emergency_contact_name="Grace Mthembu", emergency_contact_phone="075 100 2000"),
        ]
        db.session.add_all(patients)
        db.session.flush()

        # Appointments
        today = date.today()
        appointments = [
            Appointment(patient_id=patients[0].id, doctor_id=doctors[0].id, appointment_date=today, appointment_time=time(9, 0), duration_minutes=30, reason="Annual check-up", status="Scheduled"),
            Appointment(patient_id=patients[1].id, doctor_id=doctors[2].id, appointment_date=today, appointment_time=time(10, 30), duration_minutes=30, reason="Follow-up consultation", status="Confirmed"),
            Appointment(patient_id=patients[2].id, doctor_id=doctors[1].id, appointment_date=today + timedelta(days=1), appointment_time=time(14, 0), duration_minutes=45, reason="Chest pain evaluation", status="Scheduled"),
            Appointment(patient_id=patients[3].id, doctor_id=doctors[0].id, appointment_date=today + timedelta(days=2), appointment_time=time(11, 0), duration_minutes=30, reason="Flu symptoms", status="Scheduled"),
            Appointment(patient_id=patients[4].id, doctor_id=doctors[1].id, appointment_date=today - timedelta(days=1), appointment_time=time(8, 30), duration_minutes=60, reason="Blood pressure monitoring", status="Completed"),
            Appointment(patient_id=patients[0].id, doctor_id=doctors[2].id, appointment_date=today - timedelta(days=3), appointment_time=time(15, 0), duration_minutes=30, reason="Vaccination", status="Completed"),
            Appointment(patient_id=patients[1].id, doctor_id=doctors[0].id, appointment_date=today - timedelta(days=5), appointment_time=time(9, 30), duration_minutes=30, reason="Skin rash consultation", status="Cancelled"),
        ]
        db.session.add_all(appointments)
        db.session.flush()

        # Invoices (for cash-paying patient Fatima Ismail)
        invoices = [
            Invoice(
                invoice_number="INV1001",
                patient_id=patients[3].id,
                invoice_date=today - timedelta(days=5),
                due_date=today - timedelta(days=5) + timedelta(days=30),
                payment_method="CASH",
                status="Paid",
                notes="Payment received at reception.",
            ),
            Invoice(
                invoice_number="INV1002",
                patient_id=patients[3].id,
                invoice_date=today - timedelta(days=1),
                due_date=today + timedelta(days=29),
                payment_method="EFT",
                status="Unpaid",
            ),
        ]
        db.session.add_all(invoices)
        db.session.flush()

        # Invoice items
        items = [
            InvoiceItem(invoice_id=invoices[0].id, description="General Consultation", quantity=1, unit_price=650.00),
            InvoiceItem(invoice_id=invoices[0].id, description="Blood Test", quantity=1, unit_price=350.00),
            InvoiceItem(invoice_id=invoices[1].id, description="Follow-up Consultation", quantity=1, unit_price=450.00),
            InvoiceItem(invoice_id=invoices[1].id, description="Prescription Medication", quantity=2, unit_price=120.00),
        ]
        db.session.add_all(items)

        db.session.commit()
        print("Database seeded successfully!")
        print("  Login credentials:  admin / admin123")


if __name__ == "__main__":
    seed()
