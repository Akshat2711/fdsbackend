from flask import Flask, request, jsonify
from flask_cors import CORS
from apify_client import ApifyClient
import os
from dotenv import load_dotenv
import logging
import concurrent.futures

load_dotenv()
apikey = os.getenv("apifykey")
app = Flask(__name__)
CORS(app)

logging.basicConfig(level=logging.INFO)

@app.route('/extract-text', methods=['POST'])
def extract_text():
    try:
        data = request.get_json()
        points = data.get('points', [])
        if not points:
            return jsonify({'error': 'No points provided'}), 400

        logging.info(f"Received points: {points}")

        client = ApifyClient(apikey)
        all_job_results = []

        def process_point(point):
            run_input = {
                "position": point,
                "country": "IN",
                "location": "chennai",
                "maxItems": 1,
                "parseCompanyDetails": False,
                "saveOnlyUniqueItems": True,
                "followApplyRedirects": False,
            }
            run = client.actor("hMvNSpz3JnHgl5jkh").call(run_input=run_input)
            job_results = []
            for item in client.dataset(run["defaultDatasetId"]).iterate_items():
                job_results.append([
                    item['positionName'],
                    item['salary'],
                    item['jobType'],
                    item['company'],
                    item['location'],
                    item['rating'],
                    item['description'],
                    item['externalApplyLink'],
                ])
            return job_results

        with concurrent.futures.ThreadPoolExecutor() as executor:
            results = list(executor.map(process_point, points))
            for job_results in results:
                all_job_results.extend(job_results)

        return jsonify({'points_received': points, 'job_results': all_job_results}), 200

    except Exception as e:
        logging.error(f"Error processing request: {str(e)}")
        return jsonify({'error': 'Internal Server Error', 'details': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=False, port=5000)
