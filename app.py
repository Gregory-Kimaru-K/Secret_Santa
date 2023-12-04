from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(80), unique = True, nullable = False)
    password = db.Column(db.String(40), unique = True, nullable = False)

def create_tables():
    with app.app_context():
        db.create_all()

@app.route("/signin", methods = ['GET', 'POST'])
def signin():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        new_user = User(username=username, password=password)
        db.session.add(new_user)
        db.session.commit()
        
        return redirect(url_for('success'))

    return render_template('signin.html')

@app.route("/success")
def success():
    return 'Registration successful'
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/login")
def login():
    return render_template('login.html')


@app.route("/santato")
def santato():
    return render_template("results.html")

@app.route("/users")
def show_users():
    users = User.query.all()
    return render_template("users.html", users = users)

if __name__ == '__main__':
    create_tables()
    app.run(debug=True)