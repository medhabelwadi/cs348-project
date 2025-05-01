from flask import Flask, render_template, request, redirect, url_for
from sqlalchemy import text
from models import db, Student, Session, SessionParticipant, Location
from datetime import datetime

app = Flask(__name__)
#replace <password> with your mysql password
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:<password>@localhost/tutoring_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

with app.app_context():
    db.create_all()

@app.route("/report", methods=["GET", "POST"])
def report():
    if request.method == "POST":
        start_date = request.form.get("start_date")
        end_date = request.form.get("end_date")
        tutor_id = request.form.get("tutor_id")
        location_id = request.form.get("location_id") or None

        sql = text("""
        SELECT s.subject, s.date, s.time, s.duration, l.room, COUNT(sp.student_id) as tutees
        FROM sessions s
        JOIN locations l ON s.location_id = l.location_id
        JOIN session_participants sp ON s.session_id = sp.session_id AND sp.is_tutor = FALSE
        JOIN session_participants tutor ON s.session_id = tutor.session_id AND tutor.is_tutor = TRUE
        WHERE s.date BETWEEN :start_date AND :end_date
          AND tutor.student_id = :tutor_id
          AND (:location_id IS NULL OR s.location_id = :location_id)
        GROUP BY s.session_id, s.subject, s.date, s.time, s.duration, l.room
        """)

        result = db.session.execute(sql, {
            'start_date': start_date,
            'end_date': end_date,
            'tutor_id': tutor_id,
            'location_id': location_id
        }).fetchall()

        total_sessions = len(result)
        total_duration = sum([r.duration for r in result])
        total_tutees = sum([r.tutees for r in result])

        return render_template("report.html",
                               sessions=result,
                               total_sessions=total_sessions,
                               avg_duration=total_duration / total_sessions if total_sessions else 0,
                               total_tutees=total_tutees,
                               avg_tutees=total_tutees / total_sessions if total_sessions else 0)

    # GET request: show the form
    tutors = db.session.query(Student).join(SessionParticipant).filter(SessionParticipant.is_tutor == True).distinct().all()
    locations = Location.query.all()
    return render_template("report_form.html", tutors=tutors, locations=locations)


@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        subject = request.form['subject']
        date = datetime.strptime(request.form['date'], '%Y-%m-%d').date()
        time = datetime.strptime(request.form['time'], '%H:%M').time()
        duration = int(request.form['duration'])
        location_id = int(request.form['location'])
        tutor_id = int(request.form['tutor_id'])
        tutee_ids = request.form.getlist('tutee_ids')

        new_session = Session(subject=subject, date=date, time=time, duration=duration, location_id=location_id)
        db.session.add(new_session)
        db.session.commit()

        db.session.add(SessionParticipant(session_id=new_session.session_id, student_id=tutor_id, is_tutor=True))

        for tutee_id in tutee_ids:
            if int(tutee_id) == tutor_id:
                continue
            db.session.add(SessionParticipant(session_id=new_session.session_id, student_id=int(tutee_id), is_tutor=False))

        db.session.commit()
        return redirect(url_for('home'))

    locations = Location.query.all()
    students = Student.query.all()

    sessions = Session.query.all()
    session_data = []
    for s in sessions:
        location = Location.query.get(s.location_id)
        participants = SessionParticipant.query.filter_by(session_id=s.session_id).all()
        tutor = next((Student.query.get(p.student_id) for p in participants if p.is_tutor), None)
        tutees = [Student.query.get(p.student_id) for p in participants if not p.is_tutor]
        session_data.append({
            'session': s,
            'location': location,
            'tutor': tutor,
            'tutees': tutees
        })

    return render_template('home.html', locations=locations, students=students, sessions=session_data)
@app.route('/delete_session/<int:session_id>', methods=['POST'])
def delete_session(session_id):
    # Delete all participants for this session
    SessionParticipant.query.filter_by(session_id=session_id).delete()
    # Then delete the session itself
    Session.query.filter_by(session_id=session_id).delete()
    db.session.commit()
    return redirect(url_for('home'))

@app.route('/edit_session/<int:session_id>', methods=['GET', 'POST'])
def edit_session(session_id):
    session = Session.query.get_or_404(session_id)

    if request.method == 'POST':
        # Update session details
        session.subject = request.form['subject']
        session.date = datetime.strptime(request.form['date'], '%Y-%m-%d').date()
        session.time = datetime.strptime(request.form['time'], '%H:%M').time()
        session.duration = int(request.form['duration'])
        session.location_id = int(request.form['location'])
        db.session.commit()

        # Remove old participants
        SessionParticipant.query.filter_by(session_id=session_id).delete()

        # Add updated tutor and tutees
        tutor_id = int(request.form['tutor_id'])
        tutee_ids = request.form.getlist('tutee_ids')

        db.session.add(SessionParticipant(session_id=session_id, student_id=tutor_id, is_tutor=True))
        for tutee_id in tutee_ids:
            if int(tutee_id) == tutor_id:
                continue
            db.session.add(SessionParticipant(session_id=session_id, student_id=int(tutee_id), is_tutor=False))

        db.session.commit()
        return redirect(url_for('home'))

    # For GET request (display form)
    locations = Location.query.all()
    students = Student.query.all()
    participants = SessionParticipant.query.filter_by(session_id=session_id).all()
    tutor_id = next((p.student_id for p in participants if p.is_tutor), None)
    tutee_ids = [p.student_id for p in participants if not p.is_tutor]

    return render_template('edit_session.html',
                           session=session,
                           locations=locations,
                           students=students,
                           tutor_id=tutor_id,
                           tutee_ids=tutee_ids)

#with app.app_context():
    #db.create_all()

if __name__ == '__main__':
    app.run(debug=True)
