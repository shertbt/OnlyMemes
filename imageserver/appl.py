import requests
import json
from flask import Flask, request, jsonify, make_response,abort,send_file
import os
import time
from hashlib import md5
import io
from base64 import b64encode
from PIL import Image

MAX_CONTENT_LENGTH = 16 * 1024 * 1024
ALLOWED_EXTENSIONS= ['jpg', 'png']

app = Flask(__name__)
os.makedirs(os.path.join(app.root_path, 'static\\uploads'), exist_ok=True)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_image(image):
    image_name=image.filename
    random_hex = md5(time.strftime("%Y%m%d-%H%M%S").encode()).hexdigest()
    name,ext = os.path.splitext(image_name)
    image_fn = random_hex + ext
    path = os.path.join(app.root_path, 'static\\uploads', image_fn)

    image.save(path)

    return image_fn



@app.route('/upload', methods=['POST'])
def upload():
    
    try:
        image = request.files['file']
        
        if image and allowed_file(image.filename):
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


@app.route('/download/<image_name>', methods=['GET'])
def download(image_name):
  
    try:
        path = os.path.join(app.root_path, 'static\\uploads', image_name)
        if not os.path.exists(path):
            raise ValueError
        return send_file(path)
       
    except ValueError:
        response = {'status': 'Error'}
        response['message'] = 'Image not found'
        return make_response(jsonify(response), 404)
    
@app.route('/delete/<image_name>', methods=['GET'])
def delete(image_name):
    
    try:
        path = os.path.join(app.root_path, 'static\\uploads', image_name)
        if not os.path.exists(path):
            raise ValueError
        os.unlink(path)
        response = {'image_name': image_name, 'status': 'OK'}
        response['message'] = 'Image succesfully deleted'
        return make_response(jsonify(response), 200)
    except ValueError:
        response = {'status': 'Error'}
        response['message'] = 'Image not found'
        app.logger.info(response['message'])
        return make_response(jsonify(response), 404)

if __name__ == '__main__':
    app.run(debug=True,host='127.0.0.1', port=8080 )