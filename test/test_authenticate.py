import json
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
        # mypath: str = os.path.dirname(__file__)
        # parent_dir_path = mypath.replace('\\test', '')
        # self.test_server_process = subprocess.Popen(
        #     r'C:\Users\furim\PycharmProjects\robochichi\venv\Scripts\python.exe %s' % (os.path.join(parent_dir_path, 'robochichi.py')),
        # )
        pass

    def __del__(self):
        pass
        # self.test_server_process.kill()

    def test_hashpw(self):
        pwhash = robochichi.hashpw('pasuwado', 'testsalt')
        self.assertEqual(
            pwhash,
            'db053c7d6932bf805b4ca9f5b6f0b3f42ccaed690b8c5df6f7032fefd8f95f15'
        )

    def test_user_info(self):
        user_info = robochichi.user_info('furimura@gmail.com')
        self.assertEqual(user_info.get('user_id'), 1)

        user_info = robochichi.user_info('invalidid')
        self.assertIsNone(user_info)

    def test_log_in(self):
        response = requests.post(
            url='http://127.0.0.1:5000/login',
            headers={'Content-Type': 'application/json'},
            data=json.dumps(
                {'username': 'furimura@gmail.com',
                 'password': 'pasuwado'}
            ).encode('utf-8')
        )
        print(response.text)
        pass

if __name__ == '__main__':
    unittest.main()
