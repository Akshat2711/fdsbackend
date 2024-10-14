from flask import Flask, request, jsonify
from flask_cors import CORS
from apify_client import ApifyClient
import os
from dotenv import load_dotenv
import logging
# Load environment variables
load_dotenv()
apikey = os.getenv("apifykey")



app = Flask(__name__)
CORS(app)

@app.route('/extract-text', methods=['POST'])
def extract_text():
    try:
        # Retrieve the points array from the incoming JSON request
        data = request.get_json()
        points = data.get('points', [])

        if not points:
            return jsonify({'error': 'No points provided'}), 400

        print(f"Received points: {points}")  # Log the points array

        # Initialize the ApifyClient with your API token
        client = ApifyClient(apikey)

        # List to hold job results for all points
        all_job_results = []

        # Process each point
        for point in points:
            # Prepare the Actor input for the current point
            run_input = {
                "position": point,
                "country": "IN",
                "location": "chennai",
                "maxItems": 1,
                "parseCompanyDetails": False,
                "saveOnlyUniqueItems": True,
                "followApplyRedirects": False,
            }

            # Run the Actor and wait for it to finish
            run = client.actor("hMvNSpz3JnHgl5jkh").call(run_input=run_input)

            # Fetch and process Actor results for the current point
            job_results = []
            for item in client.dataset(run["defaultDatasetId"]).iterate_items():
                content = [
                    item['positionName'],
                    item['salary'],
                    item['jobType'],
                    item['company'],
                    item['location'],
                    item['rating'],
                    item['description'],
                    item['externalApplyLink'],
                ]
                job_results.append(content)

            # Append job results for the current point to the overall results
            all_job_results.extend(job_results)
            break

        # Return all job results combined with the points
        print(all_job_results)
        return jsonify({'points_received': points, 'job_results': all_job_results}), 200

    except Exception as e:
        logging.error(f"Error processing request: {str(e)}")
        return jsonify({'error': 'Internal Server Error', 'details': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
