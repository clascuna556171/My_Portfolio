from flask import Flask
from flask_mysqldb import MySQL
import os

mysql = MySQL()


def create_app():
    # 1. Get the path of the main project folder
    project_root = os.getcwd()
    template_path = os.path.join(project_root, 'View')

    # --- NEW: Define Static Folder Path ---
    # We explicitly tell Flask where the static folder is (inside Website)
    static_path = os.path.join(project_root, 'Website', 'static')

    app = Flask(__name__, template_folder=template_path, static_folder=static_path)

    app.config['SECRET_KEY'] = 'dev_key_123'

    # --- NEW: Upload Configuration ---
    # Where to save images?
    app.config['UPLOAD_FOLDER'] = os.path.join(static_path, 'uploads')
    # Max file size: 16MB
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

    # Database Configuration
    app.config['MYSQL_HOST'] = 'localhost'
    app.config['MYSQL_USER'] = 'root'
    app.config['MYSQL_PASSWORD'] = ''
    app.config['MYSQL_DB'] = 'portfolio_db'

    mysql.init_app(app)

    from Controller.views import views
    app.register_blueprint(views, url_prefix='/')

    return app