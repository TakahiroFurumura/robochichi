from flask import Flask, request, jsonify
import logger

app = Flask(__name__)
logger = logger.get_logger('robochichi')

@app.route("/")
def top():
    return "<p>top</p>"


@app.route("/test")
def test():
    logger.info('GET' if request.method == 'GET'
                else 'POST' if request.method == 'POST'
                else 'neither GET nor POST')
    logger.info('HEADER:' + str(dict(request.headers)))
    logger.info('BODY(JSON):' + str(request.get_data()))
    return jsonify(str(request))


@app.route("/chatapi/line")
def line():
    logger.info('GET' if request.method == 'GET'
                else 'POST' if request.method == 'POST'
                else 'neither GET nor POST')
    logger.info('HEADER:' + str(dict(request.headers)))
    logger.info('BODY(JSON):' + str(dict(request.get_json())))

    return "<p>line response</p>"


if __name__ == '__main__':
    app.run()