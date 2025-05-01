from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Index

db = SQLAlchemy()

class Student(db.Model):
    __tablename__ = 'students'
    student_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)

class Location(db.Model):
    __tablename__ = 'locations'
    location_id = db.Column(db.Integer, primary_key=True)
    room = db.Column(db.String(50))
    building = db.Column(db.String(100))

class Session(db.Model):
    __tablename__ = 'sessions'
    session_id = db.Column(db.Integer, primary_key=True)
    subject = db.Column(db.String(100), nullable=False)
    date = db.Column(db.Date, nullable=False)
    time = db.Column(db.Time, nullable=False)
    duration = db.Column(db.Integer, nullable=False)
    location_id = db.Column(db.Integer, db.ForeignKey('locations.location_id'))

    __table_args__ = (
        Index('idx_session_date', 'date'),
        Index('idx_session_location', 'location_id'),
        Index('idx_date_location', 'date', 'location_id'),
    )

class SessionParticipant(db.Model):
    __tablename__ = 'session_participants'
    session_id = db.Column(db.Integer, db.ForeignKey('sessions.session_id'), primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.student_id'), primary_key=True)
    is_tutor = db.Column(db.Boolean, nullable=False)

    __table_args__ = (
        Index('idx_session_is_tutor', 'session_id', 'is_tutor'),
        Index('idx_participant_student', 'student_id'),
    )
