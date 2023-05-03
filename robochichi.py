from flask import Flask

app = Flask(__name__)

@app.route("/")
def top():
    return "<p>top</p>"

@app.route("/chatapi/line")
def line():
    return "<p>line response</p>"
