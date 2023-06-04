import json
import mariadb


def get_db_connection(
        host: str,
        user: str,
        password: str,
        database_name: str = None,
        port: int = 3306):

    connection = mariadb.connect(
        host=host,
        port=int(port),
        user=user,
        password=password,
        database=database_name)
    connection.auto_reconnect = True
    cursor = connection.cursor()

    return connection, cursor
