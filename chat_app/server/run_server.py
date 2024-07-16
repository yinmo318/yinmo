from waitress import serve
from server import app
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('waitress')
logger.info('Starting server...')

if __name__ == '__main__':
    serve(app, host='0.0.0.0', port=5001)