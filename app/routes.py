from flask import Blueprint, request, jsonify
from flask_cors import CORS
import cloudinary.uploader
from pymongo import MongoClient
from bson import ObjectId
import os
import jwt
import datetime
from functools import wraps
from werkzeug.security import check_password_hash, generate_password_hash

main = Blueprint('main', __name__)

CORS(main)

client = MongoClient(os.getenv("MONGO_URI"))
db = client["portfolio"]
projects_collection = db["projects"]
users_collection = db["users"]

cloudinary.config(
    cloud_name=os.getenv("CLOUD_NAME"),
    api_key=os.getenv("API_KEY"),
    api_secret=os.getenv("API_SECRET")
)

JWT_SECRET = os.getenv("JWT_SECRET", "aayumats")

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

@main.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400

    user = users_collection.find_one({"username": username})
    if not user or not check_password_hash(user["password"], password):
        return jsonify({"error": "Invalid username or password"}), 401

    token = jwt.encode({
        "username": username,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=2)
    }, JWT_SECRET, algorithm="HS256")

    return jsonify({"message": "Login successful", "token": token}), 200

@main.route('/add-project', methods=['POST'])
@token_required
def add_project():
    data = request.form
    title = data.get('title')
    description = data.get('description')
    github_url = data.get('github_url')
    website_url = data.get('website_url')
    image_file = request.files.get('image')

    if not title or not description or not image_file:
        return jsonify({"error": "Title, description, image are required"}), 400

    if github_url and not github_url.startswith('https://github.com'):
        return jsonify({"error": "GitHub URL must start with https://github.com"}), 400

    if website_url and not website_url.startswith('http'):
        return jsonify({"error": "Website URL must start with http or https"}), 400

    try:
        response = cloudinary.uploader.upload(image_file)
        image_url = response['secure_url']
    except Exception as e:
        return jsonify({"error": f"Image upload failed: {str(e)}"}), 500

    project_data = {
        "title": title,
        "description": description,
        "github_url": github_url,
        "website_url": website_url,
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
        for project in projects:
            project['_id'] = str(project['_id'])
        return jsonify({"projects": projects}), 200
    except Exception as e:
        return jsonify({"error": f"Failed to fetch projects: {str(e)}"}), 500


@main.route('/update-project/<project_id>', methods=['PUT'])
@token_required
def update_project(project_id):
    data = request.form
    title = data.get('title')
    description = data.get('description')
    github_url = data.get('github_url')
    website_url = data.get('website_url')
    new_image = request.files.get('image')

    if not title and not description and not github_url and not website_url and not new_image:
        return jsonify({"error": "No changes detected."}), 400

    project_data = {}
    if title:
        project_data["title"] = title
    if description:
        project_data["description"] = description
    if github_url:
        project_data["github_url"] = github_url
    if website_url:
        project_data["website_url"] = website_url

    if new_image:
        try:
            response = cloudinary.uploader.upload(new_image)
            project_data["image_url"] = response['secure_url']
        except Exception as e:
            return jsonify({"error": f"Image upload failed: {str(e)}"}), 500

    try:
        result = projects_collection.update_one(
            {"_id": ObjectId(project_id)},
            {"$set": project_data}
        )

        if result.matched_count == 0:
            return jsonify({"error": "Project not found"}), 404

        return jsonify({"message": "Project updated successfully!"}), 200
    except Exception as e:
        return jsonify({"error": f"Failed to update project: {str(e)}"}), 500


@main.route('/delete-project/<project_id>', methods=['DELETE'])
@token_required
def delete_project(project_id):
    try:
        project_id = ObjectId(project_id)

        result = projects_collection.delete_one({"_id": project_id})

        if result.deleted_count == 0:
            return jsonify({"error": "Project not found"}), 404

        return jsonify({"message": "Project deleted successfully!"}), 200
    except Exception as e:
        return jsonify({"error": f"Failed to delete project: {str(e)}"}), 500
