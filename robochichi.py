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
        if request.method == 'GET':
            logger.info('GET')
            logger.info('HEADER:' + str(dict(request.headers)))
            logger.info('BODY(JSON):' + str(request.get_data()))
            return 'this is robochichi.line()'
        elif request.method == 'POST':
            logger.info('POST')
        logger.info('HEADER:' + str(dict(request.headers)))
        logger.info('BODY(JSON):' + str(request.get_data()))

        # signature validation
        logger.info('signature validation')
        body = request.get_data(as_text=True)
        h = hmac.new(config.LINE_CHANNEL_SECRET.encode('utf-8'),
                     body.encode('utf-8'),
                     hashlib.sha256
                     ).digest()
        signature = base64.b64encode(h)
        # Compare x-line-signature request header and the signature
        logger.info(signature.decode())
        logger.info(request.headers.get('x-line-signature'))
        if signature.decode() == request.headers.get('x-line-signature'):
            logger.info('signature validation passed')
        else:
            logger.info('signature validation failed')
            return 'signature validation failed.'

        body_dict = dict(request.get_json())
        logger.info(str(body_dict))

        return "<p>line response</p>"
    except Exception as e:
        logger.exception(str(e))


if __name__ == '__main__':
    app.run()