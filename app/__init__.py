import os
from flask import Flask, render_template
from apscheduler.schedulers.background import BackgroundScheduler
from .config import Config
from .routes import main
import requests

def ping_server():
    try:
        server_url = os.getenv("BASE_URL", "http://localhost:5000")
        response = requests.get(server_url)
        print(f"Server pinged successfully: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"Error pinging server: {e}")

def create_app():
    app = Flask(__name__, static_folder='static', template_folder='templates')
    app.config.from_object(Config)

    app.register_blueprint(main)

    scheduler = BackgroundScheduler(daemon=True)
    scheduler.add_job(ping_server, 'interval', minutes=5)
    scheduler.start()

    @app.route('/')
    def admin():
        return render_template('index.html')

    return app
