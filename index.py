import signal
import sys
from app import create_app

app = create_app()

def handle_signal(signum, frame):
    print('Received signal:', signum)
    # Perform cleanup if needed
    sys.exit(0)

signal.signal(signal.SIGTERM, handle_signal)
signal.signal(signal.SIGINT, handle_signal)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
