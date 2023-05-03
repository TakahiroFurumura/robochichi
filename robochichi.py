from flask import Flask

app = Flask(__name__)

@app.route("/chatapi/line")
def hello_world():
    return "<p>line response</p>"
