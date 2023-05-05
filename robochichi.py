from flask import Flask, request, jsonify
import logger
import base64
import hashlib
import hmac
import config
import random
import re
from linebot import LineBotApi
from linebot.models import TextSendMessage
from linebot.exceptions import LineBotApiError

app = Flask(__name__)
logger = logger.get_logger('robochichi')
line_bot_api = LineBotApi(config.LINE_CHANNEL_ACCESS_TOKEN)

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
        events: list[dict] = body_dict.get('events')
        logger.info(str(body_dict))
        logger.debug(str(events))

        if events is not None:
            for e in events:
                if e.get('mode') == 'active':
                    if e.get('type') == 'message':
                        line_bot_api.reply_message(
                            e.get('replyToken'),
                            TextSendMessage(text=quick_reply(e.get('message').get('text')))
                        )
                    else:
                        pass


        return "<p>line response</p>"
    except Exception as e:
        logger.exception(str(e))

def quick_reply(message:str):
    if len(message) < 5:
        henji = ['へい', 'ほい', 'なんでございましょ', 'なんすか', 'へい御用ですか']
        return henji[random.randint(0, len(henji) - 1)]
    else:
        sashisuseso = ['さすが～', 'しらなかったぁ～', 'すご～～い', 'センスある～', 'そそそそそうなんだ～', 'まじ草ｗｗｗ', 'テラワロス']
        return sashisuseso[random.randint(0, len(sashisuseso) - 1)]


if __name__ == '__main__':
    app.run()