import unittest
import sys
sys.path.append('../')
import mariadb_connection
import config

class TestStringMethods(unittest.TestCase):

    def test_mariadb_connection(self):
        connection, cursor = mariadb_connection.get_db_connection(
            config.DATABASE_CRED.get('host'),
            config.DATABASE_CRED.get('user'),
            config.DATABASE_CRED.get('password')
        )
        cursor.execute('SHOW DATABASES')
        self.assertIn(('robochichi',), cursor.fetchall())

if __name__ == '__main__':
    unittest.main()
