from flask import Flask, request, jsonify, send_from_directory, Response
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import logging
import os
from dotenv import load_dotenv
import crawler

# Load configuration from environment variables
load_dotenv()
RATE_LIMIT = os.getenv('RATE_LIMIT', '5/minute')

# Configure logging
logging.basicConfig(filename='server.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__, static_folder='../client')
limiter = Limiter(app=app, key_func=get_remote_address)

@app.route('/', methods=['GET'])
def home():
    """Serve the index.html file from the static folder."""
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/find_path', methods=['POST'])
@limiter.limit(RATE_LIMIT)
def find_path():
    """Find the shortest path between two Wikipedia pages."""
    try:
        data = request.get_json()
        start_page = data['start']
        finish_page = data['finish']
        path, logs, time, discovered = crawler.find_path_async(start_page, finish_page)
        logging.info(f"Path found: {path}")
        response = jsonify({'path': path, 'logs': logs, 'time': time, 'discovered': discovered})
        return response, 200
    except crawler.PathFindingErrorWithLogs as e:
        logging.error(f"PathFindingErrorWithLogs occurred: {e}")
        return jsonify({'error': 'Timeout occurred while finding path', 'logs': e.logs, 'time': e.time, 'discovered': e.discovered}), 408
    except crawler.PathNotFoundError as e:
        logging.error(f"PathNotFoundError occurred: {e}")
        return jsonify({'error': 'No path found within the specified depth limit. Please try increasing the depth or check the start and finish pages.', 'logs': e.logs, 'time': e.time, 'discovered': e.discovered}), 404
    except Exception as e:
        logging.error(f"Error occurred: {e}")
        return jsonify({'error': 'An error occurred while finding path', 'logs': [], 'time': 0, 'discovered': 0}), 500

@app.route('/static/<path:path>')
def send_static(path):
    """Serve static files from the static folder."""
    return send_from_directory(app.static_folder, path)

@app.route('/logs', methods=['GET'])
def stream_logs():
    """Stream logs to the client."""
    def generate():
        with open('server.log', 'r') as log_file:
            while True:
                line = log_file.readline()
                if not line:
                    break
                yield f"data: {line}\n\n"
    return Response(generate(), mimetype='text/event-stream')

@app.errorhandler(Exception)
def handle_error(e):
    """Generic error handler for unhandled exceptions."""
    logging.error(f"Unhandled exception occurred: {e}")
    return jsonify({'error': 'An internal server error occurred'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, threaded=True)