from app import app, db, User, Pairing


with app.app_context():
    db.session.query(User).delete()
    db.session.query(Pairing).delete()

    db.session.commit()