from flask import Flask, request, jsonify
from flask_cors import CORS
from apify_client import ApifyClient
import os
from dotenv import load_dotenv
import logging
import concurrent.futures
import gc  # Garbage collector for manual memory management
import psutil  # For memory monitoring

# Load environment variables
load_dotenv()
apikey = os.getenv("apifykey")
app = Flask(__name__)
CORS(app)

logging.basicConfig(level=logging.INFO)

@app.route('/extract-text', methods=['POST'])
def extract_text():
    try:
        # Parse request data
        data = request.get_json()
        points = data.get('points', [])
        if not points:
            return jsonify({'error': 'No points provided'}), 400

        logging.info(f"Received points: {points}")
        client = ApifyClient(apikey)
        all_job_results = []

        # Function to process each point
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
            # Fetch only 100 items at a time (you can adjust this limit)
            for item in client.dataset(run["defaultDatasetId"]).iterate_items(limit=100):
                job_results.append([
                    item.get('positionName', 'N/A'),
                    item.get('salary', 'N/A'),
                    item.get('jobType', 'N/A'),
                    item.get('company', 'N/A'),
                    item.get('location', 'N/A'),
                    item.get('rating', 'N/A'),
                    item.get('description', 'N/A'),
                    item.get('externalApplyLink', 'N/A'),
                ])
            return job_results

        # Process in smaller batches
        batch_size = 1  # Reduced batch size to minimize memory load
        for i in range(0, len(points), batch_size):
            batch = points[i:i + batch_size]
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:  # Reduced to 1 thread
                results = list(executor.map(process_point, batch))
                for job_results in results:
                    all_job_results.extend(job_results)

            # Manually trigger garbage collection to free memory
            gc.collect()

            # Monitor memory usage after each batch
            memory = psutil.virtual_memory()
            logging.info(f"Memory usage after batch {i//batch_size + 1}: {memory.percent}%")

        return jsonify({'points_received': points, 'job_results': all_job_results}), 200

    except Exception as e:
        logging.error(f"Error processing request: {str(e)}")
        return jsonify({'error': 'Internal Server Error', 'details': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=False, port=5000)
