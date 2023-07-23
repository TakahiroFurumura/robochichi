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

    def test_get_user_info(self):
        user_info = robochichi.get_user_info('testuser@furumura-seimen.com')
        self.assertEqual(user_info.get('user_id'), 4)

        user_info = robochichi.get_user_info('invalidid')
        self.assertIsNone(user_info)

    def test_log_in(self):
        user_name = 'testuser@furumura-seimen.com'
        test_password = 'pasuwado'
        response = requests.post(
            url='http://127.0.0.1:5000/login',
            headers={'Content-Type': 'application/json'},
            data=json.dumps(
                {'username': user_name,
                 'password': test_password}
            ).encode('utf-8')
        )
        self.assertTrue(robochichi.is_valid_token(user_name, response.json()))

        # wrong password
        response2 = requests.post(
            url='http://127.0.0.1:5000/login',
            headers={'Content-Type': 'application/json'},
            data=json.dumps(
                {'username': user_name,
                 'password': test_password + 'wrongtext'}
            ).encode('utf-8')
        )
        self.assertIsNone(response2.json())
        pass

    def test_validate_token(self):
        user_info = robochichi.get_user_info('testuser@furumura-seimen.com')
        response = requests.post(
            url='http://127.0.0.1:5000/validate-token',
            headers={'Content-Type': 'application/json'},
            data=json.dumps(
                {'username': user_info.get('primary_email'),
                 'token': user_info.get('token')}
            ).encode('utf-8')
        )
        self.assertTrue(response.json().get('is_valid_token'))
        # print(response.json())

if __name__ == '__main__':
    unittest.main()
