from app import app, db
from app import User, Chat, Agent

def clear_database():
    with app.app_context():
        db.session.query(User).delete()
        db.session.query(Chat).delete()
        db.session.query(Agent).delete()
        db.session.commit()
    return("Database Erased Succesfully")

if __name__ == '__main__':
    clear_database()
