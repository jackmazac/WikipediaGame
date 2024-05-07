from flask import Flask, request, jsonify, send_from_directory, Response
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import logging
import os
from dotenv import load_dotenv
from network import AsyncHTTPClient
from search_algorithms import bidirectional_bfs, bfs
from utils import normalize_text
import asyncio

load_dotenv()
RATE_LIMIT = os.getenv('RATE_LIMIT', '5/minute')

logging.basicConfig(filename='server.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__, static_folder='../client')
limiter = Limiter(app=app, key_func=get_remote_address)

@app.route('/', methods=['GET'])
def home():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/find_path', methods=['POST'])
@limiter.limit(RATE_LIMIT)
def find_path():
    try:
        data = request.get_json()
        start_page = data['start']
        finish_page = data['finish']

        async def get_links_graph():
            async with AsyncHTTPClient() as client:
                return {
                    'Start_Page': ['Link_1', 'Link_2'],
                    'Link_1': ['Link_3', 'Link_4'],
                    'Link_2': ['Link_3'],
                    'Link_3': ['Target_Page'],
                    'Link_4': [],
                    'Target_Page': []
                }

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        graph = loop.run_until_complete(get_links_graph())

        path = bidirectional_bfs(graph, start_page, finish_page)
        if path:
            logging.info(f"Path found: {path}")
            return jsonify({'path': path, 'logs': [], 'time': 0, 'discovered': len(graph)}), 200
        else:
            logging.warning(f"No path found between {start_page} and {finish_page}")
            return jsonify({'error': 'No path found within the specified depth limit.', 'logs': [], 'time': 0, 'discovered': len(graph)}), 404

    except KeyError as e:
        logging.error(f"Key error in JSON parsing: {e}")
        return jsonify({'error': 'Improper data format', 'logs': [], 'time': 0, 'discovered': 0}), 400
    except Exception as e:
        logging.error(f"Error occurred: {e}")
        return jsonify({'error': 'An error occurred while finding path', 'logs': [], 'time': 0, 'discovered': 0}), 500

@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory(app.static_folder, path)

@app.route('/logs', methods=['GET'])
def stream_logs():
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
    logging.error(f"Unhandled exception occurred: {e}")
    return jsonify({'error': 'An internal server error occurred'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, threaded=True)
