from flask import Blueprint, request, jsonify
from flask_cors import CORS
import cloudinary.uploader
from pymongo import MongoClient
import os
import jwt
import datetime
from functools import wraps
from werkzeug.security import check_password_hash, generate_password_hash

# Initialize Flask Blueprint
main = Blueprint('main', __name__)

# Enable CORS for the main blueprint
CORS(main)

# MongoDB setup
client = MongoClient(os.getenv("MONGO_URI"))
db = client["portfolio"]
projects_collection = db["projects"]
users_collection = db["users"]  # Collection for storing admin users

# Cloudinary configuration
cloudinary.config(
    cloud_name=os.getenv("CLOUD_NAME"),
    api_key=os.getenv("API_KEY"),
    api_secret=os.getenv("API_SECRET")
)

# JWT secret key
JWT_SECRET = os.getenv("JWT_SECRET", "aayumats")

# Decorator for verifying JWT token
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({"error": "Token is missing!"}), 401
        try:
            jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token has expired!"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token!"}), 401
        return f(*args, **kwargs)
    return decorated

# Route for admin login
@main.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400

    # Fetch user from the database
    user = users_collection.find_one({"username": username})
    if not user or not check_password_hash(user["password"], password):
        return jsonify({"error": "Invalid username or password"}), 401

    # Generate JWT token
    token = jwt.encode({
        "username": username,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=2)  # Token expires in 2 hours
    }, JWT_SECRET, algorithm="HS256")

    return jsonify({"message": "Login successful", "token": token}), 200

# Route for adding a project (protected)
@main.route('/add-project', methods=['POST'])
@token_required
def add_project():
    data = request.form
    title = data.get('title')
    description = data.get('description')
    github_url = data.get('github_url')  # New field for GitHub URL
    website_url = data.get('website_url')  # New field for website URL
    image_file = request.files.get('image')

    # Ensure required fields are provided
    if not title or not description or not image_file:
        return jsonify({"error": "Title, description, image are required"}), 400

    # Validate GitHub URL (optional)
    if github_url and not github_url.startswith('https://github.com'):
        return jsonify({"error": "GitHub URL must start with https://github.com"}), 400

    # Validate website URL (optional)
    if website_url and not website_url.startswith('http'):
        return jsonify({"error": "Website URL must start with http or https"}), 400

    # Upload the image to Cloudinary
    try:
        response = cloudinary.uploader.upload(image_file)
        image_url = response['secure_url']
    except Exception as e:
        return jsonify({"error": f"Image upload failed: {str(e)}"}), 500

    # Store the project data in MongoDB
    project_data = {
        "title": title,
        "description": description,
        "github_url": github_url,  # Save GitHub URL
        "website_url": website_url,  # Save website URL
        "image_url": image_url
    }

    try:
        projects_collection.insert_one(project_data)
        return jsonify({"message": "Project added successfully!"}), 201
    except Exception as e:
        return jsonify({"error": f"Failed to save project: {str(e)}"}), 500
    

@main.route('/projects', methods=['GET'])
def get_projects():
    try:
        projects = list(projects_collection.find())
        # Remove the '_id' field from the project data before sending it to the client
        for project in projects:
            project['_id'] = str(project['_id'])  # Convert ObjectId to string for JSON serialization
        return jsonify({"projects": projects}), 200
    except Exception as e:
        return jsonify({"error": f"Failed to fetch projects: {str(e)}"}), 500

