from flask import Flask, json, request, jsonify
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.image import img_to_array
from PIL import Image
import numpy as np
import requests
import tempfile
from io import BytesIO
from datetime import datetime
from gcs_utils import upload_image_to_gcs
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Read environment variables
model_url = os.getenv("MODEL_URL")
GCS_BUCKET_NAME = os.getenv("GCS_BUCKET_NAME")

# Load the pre-trained Keras model
response = requests.get(model_url)
# Buat file sementara untuk menyimpan model
with tempfile.NamedTemporaryFile(suffix=".h5", delete=False) as tf:
    tf.write(response.content)
    model_path = tf.name
model = load_model(model_path, compile=False)

# Define the disease labels
DISEASE_LABELS = ['Argulus', 
                  'Bacterial aeromoniasis', 
                  'Bacterial gill', 
                  'Bacterial red spot',
                  'EUS',
                  'Fungal saprolegniasis',
                  'Healthy',
                  'Parasitic', 
                  'Tail and fin rot',
                  'White tail']

@app.route('/predict', methods=['POST'])
def predict():
    if 'image' not in request.files:
        return jsonify({"error": "No file part in the request"}), 200
    file = request.files['image']
    if file.filename == '':
        return jsonify({"error": "No file selected for uploading"}), 200
    if file:
        try:
            # Read the image file
            image_bytes = file.read()

            # Upload the image to GCS
            current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            destination = f"history/{current_time}_{file.filename}"
            image_url = upload_image_to_gcs(image_bytes, GCS_BUCKET_NAME, destination, file.content_type)

            # Load the image from bytes
            image = Image.open(BytesIO(image_bytes)).resize((150, 150))  # Adjust target_size as per your model's input size
            image = img_to_array(image)
            image = np.expand_dims(image, axis=0)
            image = image / 255.0  # Normalize the image

            # Make prediction
            predictions = model.predict(image)
            predicted_class = np.argmax(predictions, axis=1)
            disease_name = DISEASE_LABELS[predicted_class[0]]

            # Get additional information about the disease from external API
            disease_id = predicted_class[0]
            external_api_url = f"https://web-service-dot-medikan.et.r.appspot.com/disease/{disease_id+1}"
            response = requests.get(external_api_url)
            
            if response.status_code != 200:
                return jsonify({"error": "Failed to fetch disease information from external API"}), 500
            
            disease_info = response.json()

            # Assuming the nameUser and userId are part of the request form
            historyName = request.form.get('historyName')
            userId = request.form.get('userId')
            
            if not historyName or not userId:
                return jsonify({"error": "nameUser and userId are required"}), 200

            # Add to history
            history_data = {
                "historyName": historyName,
                "image": image_url,
                "userId": int(userId),
                "diseaseId": int(disease_id+1)
            }
            history_response = requests.post(
                "https://web-service-dot-medikan.et.r.appspot.com/users/history", 
                data=json.dumps(history_data), 
                headers={'Content-Type': 'application/json'}
            )

            print("berhasil")

            if history_response.status_code != 200:
                return jsonify({"error": "Failed to add to history"}), 500

            return jsonify({
                "status": "Success",
                "message": "Successfully predicted image and added to history",
                "image_url": image_url,
                "data": {
                    "id": disease_info['data'][0]['id'],
                    "name": disease_info['data'][0]['name'],
                    "description": disease_info['data'][0]['description'],
                    "treatment": disease_info['data'][0]['treatment'],
                    "reference": disease_info['data'][0]['reference']
                },
                }), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(
        host='0.0.0.0', 
        port=8080)