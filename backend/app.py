import os
from flask import Flask
from flask_cors import CORS
from routes.api_routes import api_bp
from config import Config
from dotenv import load_dotenv

# Load environment variables from .env file
# Try loading from backend directory first, then project root
backend_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(backend_dir)
env_backend = os.path.join(backend_dir, '.env')
env_root = os.path.join(project_root, '.env')

print("=" * 80)
print("ENVIRONMENT VARIABLE LOADING")
print("=" * 80)
print(f"Backend directory: {backend_dir}")
print(f"Project root: {project_root}")
print(f"Checking .env files:")
print(f"  - {env_backend}: {'EXISTS' if os.path.exists(env_backend) else 'NOT FOUND'}")
print(f"  - {env_root}: {'EXISTS' if os.path.exists(env_root) else 'NOT FOUND'}")

load_dotenv(env_backend)  # Try backend/.env first
load_dotenv(env_root)  # Then try project root .env

# Check if OPENAI_API_KEY was loaded
api_key = os.getenv('OPENAI_API_KEY')
if api_key:
    print(f"✓ OPENAI_API_KEY loaded: {api_key[:10]}... (length: {len(api_key)})")
else:
    print("⚠️ OPENAI_API_KEY NOT FOUND in environment variables")
    print("   The API will use simulated responses until this is set")
    print("   Create backend/.env file with: OPENAI_API_KEY=sk-your-key-here")
print("=" * 80)

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Configure CORS to allow requests from frontend
    CORS(app, resources={
        r"/api/*": {
            "origins": ["http://localhost:3000"],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"],
            "supports_credentials": True
        }
    })

    # Ensure upload directory exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Register blueprints
    app.register_blueprint(api_bp, url_prefix='/api')
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
