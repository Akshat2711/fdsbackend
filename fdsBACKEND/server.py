import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os
import pytesseract
from PIL import Image
#apify module and csv module to store data in excel
from apify_client import ApifyClient
from csv import *

app = Flask(__name__)
CORS(app)

# Specify the Tesseract executable path
pytesseract.pytesseract.tesseract_cmd = r"C:\pytesseract_python(img_to_txt)\tesseract.exe"

UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@app.route('/extract-text', methods=['POST'])
def extract_text():
    try:
        if 'image' not in request.files:
            return jsonify({'error': 'No file part in the request'}), 400

        file = request.files['image']

        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        if file:
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)

            # Perform OCR on the image
            image = Image.open(file_path)
            extracted_text = pytesseract.image_to_string(image)
#request to apipfy for jobs list and storing it in csv file
            headers = ['positionName', 'salary', 'jobType', 'company', 'location', 'rating', 'description', 'externalApplyLink']

            # Open the file with UTF-8 encoding
            with open("job_info.csv", "w+", newline="", encoding="utf-8") as f:
                w = writer(f, delimiter=',')
                w.writerow(headers)

                # Initialize the ApifyClient with your API token
                client = ApifyClient("apify_api_fo0FvRjBnAX9Ex7h78kZS9Od8ZY8EQ02ArjY")

                # Prepare the Actor input
                run_input = {
                    "position": "web developer",
                    "country": "IN",
                    "location": "chennai",
                    "maxItems": 1,
                    "parseCompanyDetails": False,
                    "saveOnlyUniqueItems": True,
                    "followApplyRedirects": False,
                }

                # Run the Actor and wait for it to finish
                run = client.actor("hMvNSpz3JnHgl5jkh").call(run_input=run_input)

                # Fetch and write Actor results to the CSV file
                for item in client.dataset(run["defaultDatasetId"]).iterate_items():
                    content = [item['positionName'], item['salary'], item['jobType'], item['company'], item['location'], item['rating'], item['description'], item['externalApplyLink']]
                    w.writerow(content)
########################################################################
#also we are returning csv file data fro here to website
            with open("job_info.csv","r",newline='') as f:
                r=reader(f)
                csv_data=[]
                for i in r:
                    csv_data.append(i)


            # Remove the image after extraction
            os.remove(file_path)
            return jsonify({'extracted_text': [extracted_text,csv_data]}), 200
    except Exception as e:
        # Log the error and return an internal server error response
        logging.error(f"Error processing image: {str(e)}")
        return jsonify({'error': 'Internal Server Error', 'details': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
