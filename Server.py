from flask import Flask, request, jsonify
from flask_cors import CORS
from apify_client import ApifyClient
import os
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()
apikey = os.getenv("apifykey")

# Initialize Flask app and logging
app = Flask(__name__)
CORS(app)
logging.basicConfig(level=logging.INFO)  # Set logging level to INFO for detailed logs

@app.route('/extract-text', methods=['POST'])
def extract_text():
    try:
        # Retrieve the points array from the incoming JSON request
        data = request.get_json()
        points = data.get('points', [])

        if not points:
            logging.warning("No points provided in the request")
            return jsonify({'error': 'No points provided'}), 400

        logging.info(f"Received points: {points}")  # Log the points array

        # Initialize the ApifyClient with your API token
        if not apikey:
            logging.error("Apify API key not found")
            return jsonify({'error': 'API key missing'}), 500

        client = ApifyClient(apikey)
        logging.info("Apify client initialized successfully")

        # List to hold job results for all points
        all_job_results = []

        # Process each point
        for point in points:
            logging.info(f"Processing point: {point}")

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

            logging.info(f"Actor input prepared: {run_input}")

            # Run the Actor and wait for it to finish
            try:
                run = client.actor("hMvNSpz3JnHgl5jkh").call(run_input=run_input)
                logging.info(f"Actor run successful, dataset ID: {run['defaultDatasetId']}")
            except Exception as e:
                logging.error(f"Error calling actor for point {point}: {str(e)}")
                return jsonify({'error': 'Actor call failed', 'details': str(e)}), 500

            # Fetch and process Actor results for the current point
            try:
                job_results = []
                for item in client.dataset(run["defaultDatasetId"]).iterate_items():
                    content = [
                        item.get('positionName', 'N/A'),
                        item.get('salary', 'N/A'),
                        item.get('jobType', 'N/A'),
                        item.get('company', 'N/A'),
                        item.get('location', 'N/A'),
                        item.get('rating', 'N/A'),
                        item.get('description', 'N/A'),
                        item.get('externalApplyLink', 'N/A'),
                    ]
                    job_results.append(content)

                logging.info(f"Job results for point {point}: {job_results}")
            except Exception as e:
                logging.error(f"Error fetching or processing dataset results for point {point}: {str(e)}")
                return jsonify({'error': 'Dataset processing failed', 'details': str(e)}), 500

            # Append job results for the current point to the overall results
            all_job_results.extend(job_results)

            # If you only want to process the first point, you can uncomment the break statement
            # break

        # Return all job results combined with the points
        logging.info(f"Final job results: {all_job_results}")
        return jsonify({'points_received': points, 'job_results': all_job_results}), 200

    except Exception as e:
        logging.error(f"Error processing request: {str(e)}")
        return jsonify({'error': 'Internal Server Error', 'details': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
