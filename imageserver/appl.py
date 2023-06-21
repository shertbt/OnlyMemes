import requests
import json
from flask import Flask, request, jsonify, make_response,send_from_directory
import os
import secrets
from PIL import Image

MAX_CONTENT_LENGTH = 1024 * 1024
UPLOAD_EXTENSIONS= ['.jpg', '.png', '.gif']

app = Flask(__name__)

def allowed_file(filename):
	return '.' in filename and filename.rsplit('.', 1)[1].lower() in UPLOAD_EXTENSIONS

def save_image(image):
    image_name=image.filename
    random_hex = secrets.token_hex(16)
    name,ext = os.path.splitext(image_name)
    image_fn = random_hex + ext
    path = os.path.join(app.root_path, 'static\\uploads', image_fn)

    image.save(path)

    return image_fn

@app.route('/upload', methods=['POST'])
def upload():
    """
    Upload an image into the image store
    
    """
    try:
        image = request.files['file']
        if image:
            
            name=save_image(image)
            response = {'image_name': name, 'status': 'OK'}
            response['message'] = 'Image succesfully uploaded'
            return make_response(jsonify(response), 200)
        else:
            raise TypeError
    except TypeError:
        response = {'status': 'Error'}
        response['message'] = 'Unsupported file type'
        return make_response(jsonify(response), 415)
    except Exception as e:
        response = {'status': 'Error'}
        response['message'] = 'Failed to upload image'
        return make_response(jsonify(response), 500)

def get_image(filename):
    return send_from_directory(os.path.join(app.root_path, 'static\\uploads'), filename)

@app.route('/download/<image_name>', methods=['GET'])
def download(image_name):
    """
    Download an uploaded image from the image store
    
    """
    try:
        
        image = get_image(image_name)
        if not image:
            raise ValueError
        return image
    
    except ValueError:
        response = {'status': 'Error'}
        response['message'] = 'Image not found'
        app.logger.info(response['message'])
        return make_response(jsonify(response), 404)
    
@app.route('/delete/<image_name>', methods=['GET'])
def delete(image_name):
    try:
        os.unlink(os.path.join(app.root_path, 'static\\uploads', image_name))
        response = {'image_name': image_name, 'status': 'OK'}
        response['message'] = 'Image succesfully deleted'
        return make_response(jsonify(response), 200)
    except Exception:
        response = {'status': 'Error'}
        response['message'] = 'Image not found'
        app.logger.info(response['message'])
        return make_response(jsonify(response), 404)

if __name__ == '__main__':
    app.run(debug=True,host='127.0.0.1', port=8080 )