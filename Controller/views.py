from flask import Blueprint, render_template, request, redirect, url_for, session, current_app, flash
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
from Website import mysql
import os

views = Blueprint('views', __name__)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif'}


# --- PUBLIC ROUTES ---

@views.route('/')
def home():
    cur = mysql.connection.cursor()
    # 1. Fetch Projects
    cur.execute("SELECT * FROM projects")
    projects_data = cur.fetchall()
    # 2. Fetch Certificates
    cur.execute("SELECT * FROM certificates")
    certs_data = cur.fetchall()
    # 3. Fetch Journey (Newest First)
    cur.execute("SELECT * FROM journey ORDER BY id DESC")
    journey_data = cur.fetchall()

    cur.close()
    return render_template("home.html", projects=projects_data, certificates=certs_data, journey=journey_data)


@views.route('/project/<string:id_data>')
def project_details(id_data):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM projects WHERE id = %s", (id_data,))
    data = cur.fetchone()
    cur.close()

    if not data:
        return redirect(url_for('views.home'))

    return render_template("project_details.html", project=data)


@views.route('/send-message', methods=['POST'])
def send_message():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        msg = request.form['message']

        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO messages (name, email, message) VALUES (%s, %s, %s)", (name, email, msg))
        mysql.connection.commit()
        cur.close()

        flash("Message sent successfully!", "success")
        return redirect(url_for('views.home', _anchor='contact'))


# --- AUTH ROUTES ---

@views.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cur.fetchone()
        cur.close()
        if user and check_password_hash(user[2], password):
            session['loggedin'] = True
            session['username'] = user[1]
            return redirect(url_for('views.home'))
        else:
            return "Incorrect Password"
    return render_template("login.html")


@views.route('/change-password', methods=['GET', 'POST'])
def change_password():
    if 'loggedin' not in session: return redirect(url_for('views.login'))

    if request.method == 'POST':
        current_pw = request.form['current_password']
        new_pw = request.form['new_password']
        confirm_pw = request.form['confirm_password']
        username = session['username']

        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cur.fetchone()

        # 1. Check if Current Password is correct
        if user and check_password_hash(user[2], current_pw):
            # 2. Check if New Passwords match
            if new_pw == confirm_pw:
                # 3. Hash the new password and update DB
                hashed_pw = generate_password_hash(new_pw)
                cur.execute("UPDATE users SET password_hash = %s WHERE username = %s", (hashed_pw, username))
                mysql.connection.commit()
                cur.close()
                flash("Password updated successfully!", "success")
                return redirect(url_for('views.home'))
            else:
                flash("New passwords do not match!", "danger")
        else:
            flash("Incorrect current password!", "danger")

        cur.close()

    return render_template("change_password.html")


@views.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('username', None)
    return redirect(url_for('views.home'))


# --- ADMIN ROUTES (Projects) ---

@views.route('/add', methods=['GET', 'POST'])
def add_project():
    if 'loggedin' not in session: return redirect(url_for('views.login'))

    if request.method == 'POST':
        title = request.form['title']
        desc = request.form['description']
        tech = request.form['tech_stack']
        link = request.form['github_link']
        image_filename = 'default.jpg'

        if 'image' in request.files:
            file = request.files['image']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
                image_filename = filename

        cur = mysql.connection.cursor()
        cur.execute(
            "INSERT INTO projects (title, description, tech_stack, github_link, image_filename) VALUES (%s, %s, %s, %s, %s)",
            (title, desc, tech, link, image_filename))
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('views.home'))

    return render_template("add.html")


@views.route('/edit-project/<string:id_data>', methods=['GET', 'POST'])
def edit_project(id_data):
    if 'loggedin' not in session: return redirect(url_for('views.login'))
    cur = mysql.connection.cursor()
    if request.method == 'POST':
        title = request.form['title']
        desc = request.form['description']
        tech = request.form['tech_stack']
        link = request.form['github_link']
        image_filename = request.form['old_image']
        if 'image' in request.files:
            file = request.files['image']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
                image_filename = filename
        cur.execute(
            "UPDATE projects SET title=%s, description=%s, tech_stack=%s, github_link=%s, image_filename=%s WHERE id=%s",
            (title, desc, tech, link, image_filename, id_data))
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('views.home'))

    cur.execute("SELECT * FROM projects WHERE id = %s", (id_data,))
    data = cur.fetchone()
    cur.close()
    return render_template('edit_project.html', project=data)


@views.route('/delete-project/<string:id_data>')
def delete_project(id_data):
    if 'loggedin' not in session: return redirect(url_for('views.login'))
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM projects WHERE id = %s", (id_data,))
    mysql.connection.commit()
    cur.close()
    return redirect(url_for('views.home'))


# --- ADMIN ROUTES (Certificates) ---

@views.route('/add-certificate', methods=['GET', 'POST'])
def add_certificate():
    if 'loggedin' not in session: return redirect(url_for('views.login'))
    if request.method == 'POST':
        title = request.form['title']
        issuer = request.form['issuer']
        year = request.form['year']
        link = request.form['link']
        desc = request.form['description']
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO certificates (title, issuer, description, year, link) VALUES (%s, %s, %s, %s, %s)",
                    (title, issuer, desc, year, link))
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('views.home'))
    return render_template("add_cert.html")


@views.route('/edit-certificate/<string:id_data>', methods=['GET', 'POST'])
def edit_certificate(id_data):
    if 'loggedin' not in session: return redirect(url_for('views.login'))
    cur = mysql.connection.cursor()
    if request.method == 'POST':
        title = request.form['title']
        issuer = request.form['issuer']
        year = request.form['year']
        link = request.form['link']
        desc = request.form['description']
        cur.execute("UPDATE certificates SET title=%s, issuer=%s, description=%s, year=%s, link=%s WHERE id=%s",
                    (title, issuer, desc, year, link, id_data))
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('views.home'))

    cur.execute("SELECT * FROM certificates WHERE id = %s", (id_data,))
    data = cur.fetchone()
    cur.close()
    return render_template('edit_cert.html', cert=data)


@views.route('/delete-certificate/<string:id_data>')
def delete_certificate(id_data):
    if 'loggedin' not in session: return redirect(url_for('views.login'))
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM certificates WHERE id = %s", (id_data,))
    mysql.connection.commit()
    cur.close()
    return redirect(url_for('views.home'))


# --- ADMIN ROUTES (Messages) ---

@views.route('/messages')
def view_messages():
    if 'loggedin' not in session: return redirect(url_for('views.login'))
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM messages ORDER BY date_sent DESC")
    msgs = cur.fetchall()
    cur.close()
    return render_template('messages.html', messages=msgs)


@views.route('/delete-message/<string:id_data>')
def delete_message(id_data):
    if 'loggedin' not in session: return redirect(url_for('views.login'))
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM messages WHERE id = %s", (id_data,))
    mysql.connection.commit()
    cur.close()
    return redirect(url_for('views.view_messages'))


# --- ADMIN ROUTES (Journey/Timeline) ---

@views.route('/add-journey', methods=['GET', 'POST'])
def add_journey():
    if 'loggedin' not in session: return redirect(url_for('views.login'))

    if request.method == 'POST':
        year = request.form['year']
        title = request.form['title']
        subtitle = request.form['subtitle']
        desc = request.form['description']

        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO journey (year, title, subtitle, description) VALUES (%s, %s, %s, %s)",
                    (year, title, subtitle, desc))
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('views.home'))

    return render_template("add_journey.html")


@views.route('/delete-journey/<string:id_data>')
def delete_journey(id_data):
    if 'loggedin' not in session: return redirect(url_for('views.login'))
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM journey WHERE id = %s", (id_data,))
    mysql.connection.commit()
    cur.close()
    return redirect(url_for('views.home'))


# --- ERROR HANDLERS ---

@views.app_errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404