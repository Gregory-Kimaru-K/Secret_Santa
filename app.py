from flask import Flask, render_template, redirect, url_for, request, flash, Blueprint
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_cors import CORS
import secrets
import logging
from datetime import datetime
import random 
from random import choice
from flask import jsonify
import json as flask_json
from sqlalchemy import func


app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_hex(16)  # Updated secret key
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Enable CORS for specific origins
CORS(app)

# Set up Flask-Login
login_manager = LoginManager(app)
login_manager.login_view = 'login'  # login route

# Define User model with UserMixin for Flask-Login
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    # chosen_by = db.relationship('Pairing', foreign_keys='Pairing.chosen_id', backref='chosen_user', lazy='dynamic')

    @property
    def password(self):
        raise AttributeError('Password is not a readable attribute.')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def get_pairing(self):
        return Pairing.query.filter_by(chooser_id=self.id).all()

class Pairing(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    chooser_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    chosen_id = db.Column(db.Integer, unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class CustomJSONEncoder(flask_json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, User):
            #return a dictionary of User attributes
            return {'id': obj.id, 'name':obj.name}
        return super().default(obj)
    
app.json_encoder = flask_json.JSONEncoder

#Maintaining set to store chosen user IDs
chosen_users = set()

@login_manager.user_loader
def load_user(user_id):
    return db.session.query(User).get(int(user_id))

@app.route('/register', methods=['GET', 'POST'])
def register():

    if request.method == 'POST':

        name = request.form.get('name')
        password = request.form.get('password')
        confirmpassword =request.form.get('confirmpassword')


        if len(name) < 14:
            flash('Error: Name must be atleast 14 characters long', 'error')
            return redirect(url_for('register'))

        existing_user = User.query.filter_by(name=name).first()


        if existing_user:
            flash('Account already exists.\n Please use a different name or log in.', 'error')
            return redirect(url_for('register')) 
               
        if password != confirmpassword:
            flash('Error password don\'t match', 'error')
            return redirect(url_for('register'))
        
        if len(password) < 7 or not any(char.isalpha() for char in password) or not any(char.isdigit() for char in password):
            if len(password) < 7:
                flash("Password must be more than 7 characters\n", 'error')
            
            if not any(char.isalpha() for char in password):
                flash("Password should contain  to make it more secure\n", 'error')
            
            if not any(char.isdigit() for char in password):
                flash("Password should contain numbers to make it more secure\n", 'error')

        else:
            new_user = User(name=name, password=password)
            db.session.add(new_user)
            db.session.commit()

            flash('Registration successful! You can now log in.\n', 'success')
            login_user(new_user)

            return redirect (url_for('wheel'))

    return render_template('register.html')


@app.route('/')
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        name = request.form.get('name')
        password = request.form.get('password')

        print(f"Entered username: {name}")
        print(f"Entered password: {password}")

        user = User.query.filter_by(name=name).first()

        if user:
            # User found, check password
            print(f"User found: {user.name}")

            if user.verify_password(password):
                login_user(user)
                flash(f'Welcome back, {user.name}! Login successful!\n', 'success')
                return redirect(url_for('user'))
            else:
                flash('Incorrect password. Please try again.\n', 'error')
                print("Incorrect password")
        else:
            flash('User not found.\nPlease register\n', 'error')
            print("User not found")

        # Add this line to see the entered username and password in the console
        print(f"Entered username: {name}, Entered password: {password}")

        return redirect(url_for('register'))

    return render_template('login.html')

@app.route('/user')
@login_required
def user():
    return redirect(url_for('wheel'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logout successful!', 'success')
    return redirect(url_for('login'))

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    logging.error(f"Internal Server Error: {error}")
    return render_template('500.html'), 500

@app.route('/wheel')
@login_required
def wheel():
    users = User.query.all()
    users_data = [{'id': user.id, 'name': user.name} for user in users]
    num_segments = len(users)
    # convert current_user to a serialized for mainly because local proxy cannot directly serialize to JSON
    current_user_data = {'id': current_user.id, 'name': current_user.name}

    return render_template('wheel.html', users=users_data, num_segments=num_segments, current_user=current_user_data)

@app.route("/save_pairing", methods=['POST'])
@login_required
def save_pairing():
    data = request.get_json()

    chooser_id = data.get('chooserId')

   #Check if the chooser has made a choice
    existing_pairing = Pairing.query.filter_by(chooser_id=chooser_id).first()
    if existing_pairing:
        return jsonify({"error": "Chooser has already made choice"})

    #Get a list of all users excluding the chooser
    all_users_except_chooser = User.query.filter(User.id != chooser_id).all()

    #randomly select a user from the list as the chosen one
    chosen_user = choice(all_users_except_chooser)
    chosen_id = chosen_user.id
  
    #check if chosn user has already been chosen
    if chosen_id in chosen_users:
        return jsonify({"error": "Chosen user has already been chosen"})
    
    if chosen_id == chooser_id:
        return jsonify({"error": "User cannot choose themselves"})

    #add chosen person to list of users
    chosen_users.add(chosen_id)

    new_pairing = Pairing(chooser_id=chooser_id, chosen_id=chosen_id)
    db.session.add(new_pairing)
    db.session.commit()

    print("Pairing saved successfully.")
    
    return jsonify ({"success": "Pairing saved successfully"})

#Display the current pairings
@app.route("/pairings")
@login_required
def pairings():
    pairings = Pairing.query.all()
    return render_template("pairings.html", pairings=pairings)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        # Enable HTTPS SSl (For testing not production)

        # app.run(debug=False, host="0.0.0.0", port=5000)
        app.run(debug=True)