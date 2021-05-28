#!/usr/bin/python3

import random
from flask import Flask

app = Flask(__name__)

@app.route('/')
def random_metric():
    return f"my_random_value {random.randrange(100)}"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
