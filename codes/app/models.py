# This is where we will be writing models for our database, here's a simple one for user
from datetime import datetime
from app import db, login_manager
from datetime import datetime
from flask_login import UserMixin

@login_manager.user_loader
def load_user(customer_id):
    return Customer.query.get(int(customer_id))

class Customer(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(20), nullable=False)
    def __repr__(self):
        return f"Customer('{self.email}')"


class Detect(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    image = db.Column(db.String, nullable=False)
    content = db.Column(db.Text)

    def __repr__(self):
        return f"Detect('image: {self.image}','content: {self.content}')"

class Transcribe(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    audio = db.Column(db.String, nullable=False)
    title = db.Column(db.String(120), unique=True, nullable=False)
    # content = db.Column(db.Text)

    def __repr__(self):
        return f"Transcribe('audio: {self.audio}','title: {self.title}')"