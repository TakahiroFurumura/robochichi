import unittest
import sys
sys.path.append('../')
import mariadb_connection
import config

class TestMariadbConnection(unittest.TestCase):

    def test_get_db_connection(self):
        connection, cursor = mariadb_connection.MariadbConnection.get_db_connection(
            config.DATABASE_CRED.get('host'),
            config.DATABASE_CRED.get('user'),
            config.DATABASE_CRED.get('password')
        )
        cursor.execute('SHOW DATABASES')
        self.assertIn(('robochichi',), cursor.fetchall())

    def test_init(self):
        c = mariadb_connection.MariadbConnection(
            config.DATABASE_CRED.get('host'),
            config.DATABASE_CRED.get('user'),
            config.DATABASE_CRED.get('password')
        )
        c._cursor.execute("show tables from robochichi")
        self.assertIn(('chatlog_line', ), c._cursor.fetchall())
        self.assertTrue(c._connection.connection_id)

if __name__ == '__main__':
    unittest.main()
