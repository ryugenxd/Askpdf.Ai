from flask import Flask
from flask_cors import CORS as cors
from .route import main

def create_app():
    app = Flask(__name__, static_folder='../static', template_folder='../template')
    app.config['UPLOAD_FOLDER'] = './storage'
    cors(app)
    app.register_blueprint(main)
    return app