from flask import Flask, render_template, request, redirect, url_for
from flask import flash
import secrets
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import random
from werkzeug.security import check_password_hash, generate_password_hash
import string

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(80), unique = True, nullable = False)
    password = db.Column(db.String(40), unique = True, nullable = False)
    color = db.Column(db.String(7), nullable=False)

class Pairing(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    chooser_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    chosen_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
def create_tables():
    with app.app_context():
        db.drop_all()
        db.create_all()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def generate_random_color():
    return "#{:06x}".format(random.randint(0, 0xFFFFFF))

@app.route("/signin", methods = ['GET', 'POST'])
def signin():
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            confirm_password = request.form['confirm_password']

            if len(username) <= 2:
                flash("Username must have more than 2 characters", 'danger')
                return redirect(url_for('signin'))
            
            if password != confirm_password:
                flash('Passwords do not match', 'danger')
                return redirect(url_for('signin'))

            existing_user = User.query.filter_by(username=username).first()

            if existing_user:
                flash('Account with username already exists.\nPlease choose another one', 'warning')
                return redirect(url_for('login')) 

            hashed_password = generate_password_hash(password, method='sha256')
            new_user = User(username=username, password=hashed_password, color=generate_random_color())
            db.session.add(new_user)
            try:
                db.session.commit()
            
            except Exception as e:
                db.session.rollback()
                flash(f"Error commiting to the database: {str(e)}", "danger")

            login_user(new_user)           
            flash('Registration successful', 'success')
            return redirect(url_for('home'))

        return render_template('signin.html')
    
@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()
    
        if user and check_password_hash(user.password, password):
            login_user(user)
            flash("Login successful", "success")
            return redirect(url_for('home'))
        
        else:
            flash("invalid username or password", "danger")

    return render_template('login.html')

@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash('Logout successfully','success')
    return redirect(url_for('login'))



@app.route("/success")
def success():
    return 'Registration successful'

@app.route("/")
@login_required
def home():
    users = User.query.all()
    return render_template("index.html", users=users)


@app.route("/santato")
def santato():
    return render_template("results.html")

@app.route("/users")
def show_users():
    users = User.query.all()
    return render_template("users.html", users = users)

@app.route("/wheel")
@login_required
def wheel():
    users = User.query.all()
    return render_template("wheel.html", users=users)

@app.route('/spin_wheel')
@login_required
def spin_wheel():
    users = User.query.all()
    return render_template("spin_wheel.html", users=users)

if __name__ == '__main__':
    create_tables()
    app.run(debug=True)