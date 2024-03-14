from flask import Flask, request, jsonify, send_from_directory, Response
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import requests
from bs4 import BeautifulSoup
import crawler  # Make sure crawler is properly imported or defined in the context

app = Flask(__name__, static_folder='../client')
limiter = Limiter(app=app, key_func=get_remote_address, default_limits=["5 per minute"])

@app.route('/', methods=['GET'])
def home():
    return send_from_directory(app.static_folder, 'index.html')

def extract_title(page_url):
    """
    Fetches the title of a Wikipedia page to use as target content.
    """
    try:
        response = requests.get(page_url)
        soup = BeautifulSoup(response.content, 'html.parser')
        title = soup.find('title').text
        # Optional: Clean up the title by removing ' - Wikipedia' and other unnecessary parts
        return title.replace(" - Wikipedia", "")
    except Exception as e:
        app.logger.error(f"Failed to fetch or parse page title from {page_url}: {e}")
        return None

@app.route('/find_path', methods=['POST'])
@limiter.limit("5/minute")
def find_path():
    try:
        data = request.get_json()
        start_page = data['start']
        finish_page = data['finish']

        path = crawler.find_path(start_page, finish_page)  # Updated to match crawler.py's signature
        if path is None:
            return jsonify({'error': 'Path not found'}), 404

        return jsonify({'path': path})
    except Exception as e:
        app.logger.error(f"Error occurred: {e}")
        return jsonify({'error': 'An error occurred while finding path'}), 500


@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory(app.static_folder, path)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=False)  # Set debug=False for production
