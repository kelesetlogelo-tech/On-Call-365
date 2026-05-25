from flask_wtf import FlaskForm
from wtforms import (
    DateField,
    EmailField,
    IntegerField,
    PasswordField,
    SelectField,
    StringField,
    TextAreaField,
    TimeField,
)
from wtforms.validators import DataRequired, Email, EqualTo, Length, NumberRange, Optional


class LoginForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])


class RegisterForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired(), Length(min=3, max=80)])
    email = EmailField("Email", validators=[DataRequired(), Email()])
    full_name = StringField("Full Name", validators=[DataRequired(), Length(max=150)])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField(
        "Confirm Password", validators=[DataRequired(), EqualTo("password", message="Passwords must match")]
    )


class PatientForm(FlaskForm):
    first_name = StringField("First Name", validators=[DataRequired(), Length(max=100)])
    last_name = StringField("Last Name", validators=[DataRequired(), Length(max=100)])
    date_of_birth = DateField("Date of Birth", validators=[DataRequired()])
    gender = SelectField(
        "Gender", choices=[("Male", "Male"), ("Female", "Female"), ("Other", "Other")], validators=[DataRequired()]
    )
    phone = StringField("Phone Number", validators=[DataRequired(), Length(max=20)])
    email = EmailField("Email", validators=[Optional(), Email()])
    address = TextAreaField("Address", validators=[Optional()])
    payment_type = SelectField(
        "Payment Type",
        choices=[("Medical Aid", "Medical Aid"), ("Cash", "Cash")],
        validators=[DataRequired()],
    )
    medical_aid_name = StringField("Medical Aid Name", validators=[Optional(), Length(max=100)])
    medical_aid_number = StringField("Medical Aid Number", validators=[Optional(), Length(max=50)])
    emergency_contact_name = StringField("Emergency Contact Name", validators=[Optional(), Length(max=150)])
    emergency_contact_phone = StringField("Emergency Contact Phone", validators=[Optional(), Length(max=20)])
    notes = TextAreaField("Notes", validators=[Optional()])


class DoctorForm(FlaskForm):
    first_name = StringField("First Name", validators=[DataRequired(), Length(max=100)])
    last_name = StringField("Last Name", validators=[DataRequired(), Length(max=100)])
    specialization = SelectField(
        "Specialization",
        choices=[
            ("General Practice", "General Practice"),
            ("Cardiology", "Cardiology"),
            ("Dermatology", "Dermatology"),
            ("Neurology", "Neurology"),
            ("Orthopedics", "Orthopedics"),
            ("Pediatrics", "Pediatrics"),
            ("Psychiatry", "Psychiatry"),
            ("Surgery", "Surgery"),
            ("Gynecology", "Gynecology"),
            ("Ophthalmology", "Ophthalmology"),
            ("ENT", "ENT"),
            ("Other", "Other"),
        ],
        validators=[DataRequired()],
    )
    phone = StringField("Phone Number", validators=[DataRequired(), Length(max=20)])
    email = EmailField("Email", validators=[DataRequired(), Email()])
    license_number = StringField("License / Practice Number", validators=[DataRequired(), Length(max=50)])


class AppointmentForm(FlaskForm):
    patient_id = SelectField("Patient", coerce=int, validators=[DataRequired()])
    doctor_id = SelectField("Doctor", coerce=int, validators=[DataRequired()])
    appointment_date = DateField("Date", validators=[DataRequired()])
    appointment_time = TimeField("Time", validators=[DataRequired()])
    duration_minutes = IntegerField("Duration (minutes)", default=30, validators=[DataRequired(), NumberRange(min=10, max=240)])
    reason = TextAreaField("Reason for Visit", validators=[DataRequired()])
    status = SelectField(
        "Status",
        choices=[
            ("Scheduled", "Scheduled"),
            ("Confirmed", "Confirmed"),
            ("In Progress", "In Progress"),
            ("Completed", "Completed"),
            ("Cancelled", "Cancelled"),
            ("No Show", "No Show"),
        ],
        validators=[DataRequired()],
    )
    notes = TextAreaField("Notes", validators=[Optional()])
