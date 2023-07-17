import unittest
import sys
sys.path.append('../')
import robochichi
import subprocess
import config
import requests
import os
import time

class TestAuthenticate(unittest.TestCase):

    test_server_process = None
    def setUp(self):
        """
        mypath: str = os.path.dirname(__file__)
        parent_dir_path = mypath.replace('\\test', '')
        self.test_server_process = subprocess.Popen(
            r'C:\Users\furim\PycharmProjects\robochichi\venv\Scripts\python.exe %s' % (os.path.join(parent_dir_path, 'robochichi.py')),

        )
        """

    def __del__(self):
        pass
        # self.test_server_process.kill()

    def test_hashpw(self):
        pwhash = robochichi.hashpw('pasuwado')
        self.assertEqual(
            pwhash,
            '599d4812c752a9e8030a98cda31a29b4589f8687ec994dc997c55b5b81a5b183'
        )

    def test_user_info(self):
        user_info = robochichi.user_info('furimura@gmail.com')
        self.assertEqual(user_info.get('user_id'), 1)

        user_info = robochichi.user_info('invalidid')
        self.assertIsNone(user_info)

    def test_log_in(self):
        response = requests.post(
            url='http://127.0.0.1:5000/login',
            data={'username': 'furimura@gmail.com',
                  'password': 'pasuwado'}
        )
        print(response)
        pass

if __name__ == '__main__':
    unittest.main()
