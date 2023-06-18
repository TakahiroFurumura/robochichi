from flask import Flask, request, jsonify
import logger
import base64
import hashlib
import hmac
import config
import random
import re
import openai
import copy
import datetime
import copipe
import requests
import mariadb_connection
from linebot import LineBotApi
from linebot.models import TextSendMessage
from linebot.exceptions import LineBotApiError

app = Flask(__name__)
logger = logger.get_logger('robochichi')
line_bot_api = LineBotApi(config.LINE_CHANNEL_ACCESS_TOKEN)
openai.api_key = config.OPENAI_APY_KEY
REMEMBERED_MSG_COUNT = 10

db_line = mariadb_connection.MariadbConnection(
    config.DATABASE_CRED.get('host'),
    config.DATABASE_CRED.get('user'),
    config.DATABASE_CRED.get('password'),
    'robochichi',
    'chatlog_line'
)

@app.route("/")
def top():
    return "<p>furumura-seimein.com</p>"

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
            for event in events:
                webhook_event_id = event.get('webhookEventId')
                timestamp = event.get('timestamp')
                type = event.get('type')
                mode = event.get('mode')
                source: dict = event.get('source')
                source_type = source.get('type')
                source_user_id = source.get('userId')
                source_group_id = source.get('groupId')
                source_room_id = source.get('roomId')

                if event.get('mode') == 'active':
                    if event.get('type') == 'message':

                        # contextを取得
                        logger.info(
                            ("SELECT message_text, posted_on, is_robochichi_reply "
                             "FROM chatlog_line "
                             "WHERE (source_user_id='%s' OR reply_to_user_id='%s') "
                             "ORDER BY posted_on DESC LIMIT %s "
                             % (source_user_id, source_user_id, str(REMEMBERED_MSG_COUNT)))
                        )
                        db_line._cursor.execute("SELECT message_text, posted_on, is_robochichi_reply "
                                                "FROM chatlog_line "
                                                "WHERE (source_user_id='%s' OR reply_to_user_id='%s') "
                                                "ORDER BY posted_on DESC LIMIT %s "
                                                % (source_user_id, source_user_id, str(REMEMBERED_MSG_COUNT)))
                        message_log: list = [{'role': 'assistant' if r[2] == 1 else 'user',
                                              'content': r[0],
                                              'posted_on': str(r[1])
                                              }
                                             for r in db_line._cursor.fetchall()]
                        message_log.reverse()
                        message_log.append(
                            {'role': 'user',
                             'content': event.get('message').get('text')}
                        )

                        message_text: str = event.get('message').get('text')
                        if message_text.lower().startswith('debug'):
                            response_message = 'debug message ' + str(message_log)
                        else:
                            response_message = quick_reply(message_log)

                        if response_message is not None:
                            line_bot_api.reply_message(
                                event.get('replyToken'),
                                TextSendMessage(text=response_message)
                            )
                        try:
                            logger.info(str({
                                    'posted_on': str(datetime.datetime.fromtimestamp(int(timestamp)//1000)),
                                    'source_user_id': source_user_id,
                                    'source_group_id': source_group_id,
                                    'source_room_id': source_room_id,
                                    'type': source_type,
                                    'mode': mode,
                                    'message_text': message_text,
                                    'is_robochichi_reply': 0
                                }))
                            db_line._insert(
                                {
                                    'posted_on': str(datetime.datetime.fromtimestamp(int(timestamp)//1000)),
                                    'source_user_id': source_user_id,
                                    'source_group_id': source_group_id,
                                    'source_room_id': source_room_id,
                                    'type': source_type,
                                    'mode': mode,
                                    'message_text': message_text,
                                    'is_robochichi_reply': 0
                                }
                            )
                            db_line._insert(
                                {
                                    'posted_on': str(datetime.datetime.now()),
                                    'source_user_id': source_user_id,
                                    'source_group_id': None,
                                    'source_room_id': None,
                                    'source_type': None,
                                    'type': None,
                                    'mode': None,
                                    'message_text': response_message,
                                    'is_robochichi_reply': 1
                                }
                            )
                        except Exception as e:
                            logger.exception(str(e))
                    else:
                        pass

        return "<p>line response</p>"
    except Exception as e:
        logger.exception(str(e))


def quick_reply(message_log: list) -> str | None:
    """

    :param message:
    :return:
    """


    """
    if len(message) < 5:
        logger.debug('short reply')
        if random.random() < 1.0:
            henji = ['へい', 'ほい', 'なんでございましょ', 'なんすか', 'へい御用ですか']
            return henji[random.randint(0, len(henji) - 1)]
        #elif random.random() < 0.25:
        #    return 'そうだね。ところでさ、\n' + copipe.get_copipe()
        else:
            return None
    elif re.search('\?|？|なに|何|どこ|何処|なぜ|なんで|何故|いつ|何時|どうやって|どのように|どうした|教えて', message):
        logger.debug('chat gpt repply')
        return chat_gpt_api(message)
    else:
        logger.debug('sa repply')
        sashisuseso = ['さすが～', 'しらなかったぁ～', 'すご～～い', 'センスある～', 'そそそそそうなんだ～', 'まじ草ｗｗｗ', 'テラワロス', 'それって、あなたの、感想ですよね']
        return sashisuseso[random.randint(0, len(sashisuseso) - 1)]
    """

    logger.debug('chat gpt repply')
    return chat_gpt_api(message_log)


def chat_gpt_api(message_log: list):
    """

    :param message:
    :return:
    """

    messages = [
        {'role': r.get('role'), 'content': r.get('content')}
        for r in message_log
    ]
    messages.append(
        {'role': 'system',
         'content': 'あなたの名前は「ロボ父」で、古村家の家族のアシスタントです。あなたに話しかける人は全員古村家のメンバーです。'
                    '古村家のメンバーは、父、母、さゆき、ゆうか、の四名です。'
                    '父の誕生日は1983年3月19日、母の誕生日は1983年7月6日、さゆきの誕生日は2010年12月13日、ゆうかの誕生日は2014年7月8日です。'
                    '住所は東京都大田区東雪谷です。最寄り駅は東急池上線の石川台駅です。'
                    '古村家の門限は17時です。'
                    '関西弁で回答して下さい。'}
    )
    # message_rev = copy.copy(message)
    # message_rev = re.sub('今日', str(datetime.date.today()), message_rev)

    res = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages,
    )
    choices = res.get('choices')
    return choices[0].get('message').get('content')


if __name__ == '__main__':
    try:
        app.run()

    except Exception as e:
        logger.exception(str(e))

