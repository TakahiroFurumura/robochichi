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
import hashlib
from flask_cors import CORS, cross_origin
from collections.abc import Mapping
from flask_jwt_extended import create_access_token
from flask_jwt_extended import get_jwt_identity
from flask_jwt_extended import jwt_required
from flask_jwt_extended import JWTManager

app = Flask(__name__)
app.debug = False
app.config['SECRET_KEY'] = config.SALT
CORS(app)
logger = logger.get_logger('robochichi')
line_bot_api = LineBotApi(config.LINE_CHANNEL_ACCESS_TOKEN)
openai.api_key = config.OPENAI_APY_KEY
SALT = config.SALT
REMEMBERED_MSG_COUNT = 10

db_line = mariadb_connection.MariadbConnection(
    config.DATABASE_CRED.get('host'),
    config.DATABASE_CRED.get('user'),
    config.DATABASE_CRED.get('password'),
    'robochichi',
    'chatlog_line'
)

rdbconnection = mariadb_connection.MariadbConnection(
    config.DATABASE_CRED.get('host'),
    config.DATABASE_CRED.get('user'),
    config.DATABASE_CRED.get('password'),
    'robochichi'
)


def hashpw(password: str, salt: str = None) -> str:
    m = hashlib.sha256()
    m.update(password.encode())
    m.update(salt.encode() if salt else SALT.encode())
    return m.hexdigest()


def get_user_info(primary_email: str) -> dict | None:
    """

    :param primary_email:
    :return: dict like {'user_id':, 'primary_email':, 'token':, 'password':, 'expires_on':}
    """
    rdbconnection._connection.reset()
    rdbconnection._cursor.execute(
        "SELECT users.user_id, primary_email, token, users.password, expires_on "
        "FROM robochichi.users "
        "  LEFT JOIN robochichi.tokens ON users.user_id = tokens.user_id "
        "WHERE users.primary_email = %s",
        (primary_email,)
    )
    r = rdbconnection._cursor.fetchone()
    if r:
        return dict(zip(('user_id', 'primary_email', 'token', 'password', 'expires_on'), r))
    else:
        return None


def is_valid_token(username: str, token: str):
    user = get_user_info(username)
    if user:
        if user.get('token') == token and user.get('expires_on') > datetime.datetime.now():
            return True
        else:
            return False
    else:
        return False

@app.route("/ver", methods=['POST', 'GET'])
def api_version():
    return '20230809 2151'

@app.route("/login", methods=['POST', 'GET'])
@cross_origin()
def login():
    """
    validates credential information and returns a new token if success.
    The token is saved in database table "tokens" that stores one unique token for each user_id.
    :return: {token:, userEmailId:, }
    """
    if request.method == 'GET':
        return 'POST with authentication information', 500
    elif request.method == 'POST':
        method = request.json.get('method')
        if method == 'google':
            response = {
                'token': 'testtokenforgoogleauth',
                'userEmailId': 'testemailUserId'
            }
            return jsonify(response), 200
        else:
            primary_email = request.json.get('username')
            password = request.json.get('password')
            user_info = get_user_info(primary_email)

            if user_info is None:
                return jsonify(None), 200
            else:
                # by password
                if hashpw(password) == get_user_info(primary_email).get('password'):
                    token = create_access_token(identity=primary_email)
                    token_expires_on = datetime.datetime.now() + datetime.timedelta(days=28)
                    rdbconnection._cursor.execute(
                        "INSERT INTO tokens (token, user_id, expires_on) VALUES (%s, %s, %s) "
                        "ON DUPLICATE KEY UPDATE token=%s, expires_on=%s ",
                        (token, user_info.get('user_id'), token_expires_on, token, token_expires_on))
                    rdbconnection._connection.commit()
                    return jsonify(token)
                else:
                    return jsonify(None), 200


@app.route("/validate-token", methods=['POST', 'GET'])
@cross_origin()
def validate_token():
    if request.method == 'GET':
        return 'Hi, please POST your auth.'
    elif request.method == 'POST':
        primary_email = request.json.get('username')
        token = request.json.get('token')

        if is_valid_token(primary_email, token):
            return jsonify({'is_valid_token': True})
        else:
            return jsonify({'is_valid_token': False})

    pass

jwt = JWTManager(app)


@app.route('/protected')
@jwt_required()
@cross_origin()
def protected():
    current_user = get_jwt_identity()
    return jsonify(logged_in_as=current_user), 200


@app.route("/")
@cross_origin()
def top():
    return "<p>furumura-seimein.com</p>"


@app.route("/test", methods=['GET', 'POST'])
@cross_origin()
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
         'content': config.GENERAL_CONTEXT}
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

