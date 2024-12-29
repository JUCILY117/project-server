import os
from flask import Flask, render_template
from apscheduler.schedulers.background import BackgroundScheduler
from .config import Config
from .routes import main
import requests

def ping_server():
    try:
        # Get the server URL from the environment variable
        server_url = os.getenv("BASE_URL", "http://localhost:5000")  # Default to localhost if not set
        response = requests.get(server_url)
        print(f"Server pinged successfully: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"Error pinging server: {e}")

def create_app():
    app = Flask(__name__, static_folder='static', template_folder='templates')  # Set static and template folders
    app.config.from_object(Config)

    # Register the main blueprint
    app.register_blueprint(main)

    # Set up the background scheduler
    scheduler = BackgroundScheduler(daemon=True)
    scheduler.add_job(ping_server, 'interval', minutes=5)  # Ping every 5 minutes
    scheduler.start()

    # Add route to serve the admin page
    @app.route('/')
    def admin():
        return render_template('index.html')

    return app
