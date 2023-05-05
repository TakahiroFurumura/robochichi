from flask import Flask, request, jsonify
import logger

app = Flask(__name__)
logger = logger.get_logger('robochichi')

@app.route("/")
def top():
    return "<p>top</p>"


@app.route("/test", methods=['GET', 'POST'])
def test():
    try:
        if request.method == 'GET':
            logger.info('GET')
        elif request.method == 'POST':
            logger.info('POST')
        logger.info('HEADER:' + str(dict(request.headers)))
        logger.info('BODY(JSON):' + str(request.get_data()))
        return jsonify(str(request))

    except Exception as e:
        logger.exception(str(e))


@app.route("/chatapi/line", methods=['GET', 'POST'])
def line():
    try:
        logger.info('GET' if request.method == 'GET'
                    else 'POST' if request.method == 'POST'
                    else 'neither GET nor POST')
        logger.info('HEADER:' + str(dict(request.headers)))
        logger.info('BODY(JSON):' + str(request.get_data()))

        return "<p>line response</p>"
    except Exception as e:
        logger.exception(str(e))


if __name__ == '__main__':
    app.run()