from flask import Flask, request, jsonify
import logger
import base64
import hashlib
import hmac
import config

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

        body = request.get_data()  # Request body string
        h = hmac.new(config.CHANNEL_SECRET.encode('utf-8'),
                     body.encode('utf-8'),
                     hashlib.sha256
                     ).digest()
        signature = base64.b64encode(h)
        # Compare x-line-signature request header and the signature
        logger.info('signature validation')
        logger.info(request.headers.get('x-line-signature'))
        logger.info(str(signature))

        return "<p>line response</p>"
    except Exception as e:
        logger.exception(str(e))


if __name__ == '__main__':
    app.run()