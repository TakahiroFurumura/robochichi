from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route("/")
def top():
    return "<p>top</p>"


@app.route("/test")
def test():
    message: dict = {'message': 'this is test message'}
    body = request.get_json()
    parameter = request.args.to_dict()
    return jsonify(parameter.update(body.update(message)))


@app.route("/chatapi/line")
def line():
    return "<p>line response</p>"


if __name__ == '__main__':
    app.run()