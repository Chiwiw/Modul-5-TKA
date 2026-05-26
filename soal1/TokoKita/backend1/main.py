from flask import Flask, jsonify
import socket

app = Flask(__name__)

@app.route('/')
def index():
    hostname = socket.gethostname()
    return f"Server 1 - TokoKita | Hostname: {hostname}"

@app.route('/products')
def products():
    data = [
        {"id": 1, "name": "Laptop", "price": 12000000},
        {"id": 2, "name": "Mouse", "price": 150000},
        {"id": 3, "name": "Keyboard", "price": 350000}
    ]
    return jsonify(data)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)