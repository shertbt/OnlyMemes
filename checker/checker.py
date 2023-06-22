#!/usr/bin/env python3

import datetime
import inspect
import json
import os
import random
import string
import sys
import re
from enum import Enum
from sys import argv
import requests
import names
from random_word import RandomWords
from bs4 import BeautifulSoup
from generator import string_to_bf
import pytesseract                                                                                                  
from PIL import Image, ImageDraw, ImageFont 
import shutil


random = random.SystemRandom()

""" <config> """
# SERVICE INFO
PORT = 5000
EXPLOIT_NAME = argv[0]


# DEBUG -- logs to stderr, TRACE -- log HTTP requests
DEBUG = os.getenv("DEBUG", True)
TRACE = os.getenv("TRACE", False)
""" </config> """


# check: create "about me" (3 mode) displayed for: 1)all; 2)followers; 3)only me -> get bio
# check: create post -> get post
# check: check upload image to imageserver
# check: users are displayed in searchList in two orders (reg 2 users and check them in search)
# check: followers & following are displayed
def check(host: str):
    s = FakeSession(host, PORT)
    username, email, password = create_user()
    token = sign_up(s, username, email, password)
    login(s, username, password)

    _log(f'Going to create bio "{username}"')
    bio = gen_bio()
    bio_priv = str(random.randint(1,3))
    create_bio(s, username, bio, bio_priv)
    if bio not in check_bio(s, username, bio_priv, token, host):
       die(ExitStatus.CORRUPT, "Incorrect flag")

    _log(f"Going to create post '{username}' ")
    text = gen_text()
    post_id = post_text(s, text)
    _log(f"Going to check post '{username}' as follower")
    if text not in get_post(username, token, post_id, host):
        die(ExitStatus.CORRUPT, "Incorrect flag")

    _log(f"Going to create post with image '{username}' ")
    text = gen_title()
    post_id = post_picture(s, text) 
    
    _log("Check users in searchList")
    if not check_usersList(s, username, host):
        die(ExitStatus.MUMBLE, "failed to check usersList")

    _log("Check followers & following are displayed")
    if not check_followers(s, username, host):
        die(ExitStatus.MUMBLE, "failed to check followers & following")
    die(ExitStatus.OK, "Check ALL OK")

def create_user():
    username = names.get_first_name() + "_" +generate_rand(5)
    email = f"{generate_rand(5)}@{generate_rand(5)}.{generate_rand(3)}"
    password = generate_rand(5)
    return username, email, password

def generate_rand(n=16):
    return ''.join(random.choice(string.ascii_letters) for i in range(n))

def sign_up(s, username, email, password):
    try:
        r = s.get("/sign-up") 
        csrf_token = re.search(r'<input id="csrf_token" name="csrf_token" type="hidden" value="(.*)">', r.text).group(1)
        
        r = s.post('/sign-up', data = dict(
            username = username,
            email = email,
            password = password,
            password2 = password,
            csrf_token = csrf_token
            )
        )
    
    except Exception as e:
        die(ExitStatus.DOWN, f"Failed to register in service: {e}")

    if r.status_code != 200:
        die(ExitStatus.MUMBLE, f"Unexpected /sign_up code {r.status_code}")

    try:
        token = re.search(r'Congratulations, you are now a registered user! Here is your token: (.*)', r.text).group(1)
    except Exception as e:
        die(ExitStatus.DOWN, f"Failed to get token after register in service: {e}")
    return token

def login(s, username, password):
    try:
        r = s.get('/sign-up') 
        csrf_token = re.search(r'<input id="csrf_token" name="csrf_token" type="hidden" value="(.*)">', r.text).group(1)
        r = s.post('/login', data = dict(
            username = username,      
            password = password,
            csrf_token = csrf_token
            )
        )
    except Exception as e:
        die(ExitStatus.DOWN, f"Failed to login in service: {e}")
    if r.status_code != 200:
        die(ExitStatus.MUMBLE, f"Unexpected /login code {r.status_code}")
    try:
        token = re.search(r'here is your token: (.*)', r.text).group(1)
    except Exception as e:
        die(ExitStatus.DOWN, f"Failed to get token after login in service: {e}")

def check_usersList(s, username, host):
    s2 = FakeSession(host, PORT)
    username2, email2, password2 = create_user()
    sign_up(s2, username2, email2, password2)
 
    try:
        r = s.post('/search', data = {'search':username2, 'order':'username'}) 
    except Exception as e:
        die(ExitStatus.DOWN, f"Failed to get usersList order by name: {e}")

    try:
        r = s.post('/search', data = {'search':username2, 'order':'date_created'})   
    except Exception as e:
        die(ExitStatus.DOWN, f"Failed to get usersList order by date of registration: {e}")

    if r.status_code != 200:
        die(ExitStatus.MUMBLE, f"Unexpected /search code {r.status_code}")

    if username in r.text:
        if username2 not in r.text:
            _log(f"Cant find this user {username2} in usersList")
            _log("Find first, but not find second")
            return False 
        else:
            return True
    else:
        _log(f"Cant find this user {username} in usersList")
        return False
    
def check_followers(s, username, host):
    s2 = FakeSession(host, PORT)
    username2, email2, password2 = create_user()
    token2 = sign_up(s2, username2, email2, password2)

    try:
        r = s.get('/home') 
        csrf_token = re.search(r'<input id="csrf_token" name="csrf_token" type="hidden" value="(.*)">', r.text).group(1)
        r = s.post(f'/follow/{username2}', data = {'token': token2, 'csrf_token':csrf_token})
    except Exception as e:
        die(ExitStatus.DOWN, f"Failed to follow user {username2}: {e}")

    if r.status_code != 200:
        die(ExitStatus.MUMBLE, f"Unexpected /follow/{username2} code {r.status_code}")

    try:
        r = s.get(f'/user/{username2}/followers')
    except Exception as e:
        die(ExitStatus.DOWN, f"Failed to get user {username2} followers: {e}")

    if r.status_code != 200:
        die(ExitStatus.MUMBLE, f"Unexpected /user/{username2}/followers code {r.status_code}")

    if username not in r.text:
        _log(f"Cant find this user {username} in {username2} followers")
        return False

    try:
        r = s.get(f'/user/{username}/following')
    except Exception as e:
        die(ExitStatus.DOWN, f"Failed to get user {username} following: {e}")

    if r.status_code != 200:
        die(ExitStatus.MUMBLE, f"Unexpected /user/{username}/following code {r.status_code}")

    if username2 not in r.text:
        _log(f"Cant find this user {username2} in {username} following")
        return False
    return True

def post_text(s, flag):
    r = s.get('/create-post') 
    csrf_token = re.search(r'<input id="csrf_token" name="csrf_token" type="hidden" value="(.*)">', r.text).group(1)
    try:
        title = gen_title()
        
        r = s.post("/create-post", data = dict(title = title, text = flag, csrf_token = csrf_token))
    except Exception as e:
        die(ExitStatus.DOWN, f"Failed to put flag in service: {e}")

    if r.status_code != 200:
        die(ExitStatus.MUMBLE, f"Unexpected  /create-post code {r.status_code}")

    post_id = re.search(r'<a href="/post/(.*)" class="btn btn-outline-secondary"> View post </a>', r.text).group(1)
    return post_id

def get_post(username, token, post_id, host):
    s2 = FakeSession(host, PORT)
    try:
        r2 = s2.get(f"/post/{post_id}")
    except Exception as e:
        die(ExitStatus.DOWN, f"Failed to get my post: {e}")
    if r2.status_code != 200:
        die(ExitStatus.MUMBLE, f"Unexpected  /post/{post_id} code {r2.status_code}")

    
    username2, email2, password2 = create_user()

    token2 = sign_up(s2, username2, email2, password2)
    login(s2, username2, password2)

    r2 = s2.get('/home') 
    csrf_token = re.search(r'<input id="csrf_token" name="csrf_token" type="hidden" value="(.*)">', r2.text).group(1)
    r2 = s2.post(f'/follow/{username}', data = {'token': token, 'csrf_token':csrf_token})

    try:
        r2 = s2.get(f"/post/{post_id}")
    except Exception as e:
        die(ExitStatus.DOWN, f"Failed to get {username} post: {e}")
    if r2.status_code != 200:
        die(ExitStatus.MUMBLE, f"Unexpected  /post/{post_id} code {r.status_code}")

    soup = BeautifulSoup(r2.text, 'html.parser')
    text  = [a.text for a in soup.find_all("p", class_ = "card-text")]
    
    return text
    
def gen_title():
    text = ["Funny", "kek", "Best joke", "Смехота", "Я на полу", "РЖУНЕМАГУ", "Вовочка", "Моей маме нравится", "Мое любимое",
            "анекдот", "Жиза", "LoL", "Cool", "Прислала бабушка с вацапа", "И это по твоему смешно?", "Кароче.."]
    return f"{random.choice(text)}"

def gen_text():
    with open('jokes.txt') as f:
        text = f.read().splitlines()
    return random.choice(text)

def create_bio(s, username, bio, bio_priv):
    try:
        r = s.get("/edit_profile")
    except Exception as e:
        die(ExitStatus.DOWN, f"Failed to get edit profile: {e}")
    if r.status_code != 200:
        die(ExitStatus.MUMBLE, f"Unexpected /edit_profile code {r.status_code}")

    csrf_token = re.search(r'<input id="csrf_token" name="csrf_token" type="hidden" value="(.*)">', r.text).group(1)
    try:
        r = s.post("/edit_profile", data = dict(username = username, about_me = bio, about_me_privacy = bio_priv, csrf_token = csrf_token))  
    except Exception as e:
        die(ExitStatus.DOWN, f"Failed to create bio: {e}")
    if r.status_code != 200:
        die(ExitStatus.MUMBLE, f"Unexpected /edit_profile code {r.status_code}")

def check_bio(s, username, bio_priv, token = "", host = ""):
    
    if bio_priv == "1" or bio_priv == "2":
        s2 = FakeSession(host, PORT)
        username2, email2, password2 = create_user()
        token2 = sign_up(s2, username2, email2, password2)
        login(s2, username2, password2)

    if bio_priv == "1":
        _log(f"Going to check '{username}' bio as non-follower")
        try:
            r2 = s2.get(f"/user/{username}")
        except Exception as e:
            die(ExitStatus.DOWN, f"Failed to get {username} account: {e}")
        if r2.status_code != 200:
            die(ExitStatus.MUMBLE, f"Unexpected /user/{username} {r.status_code}")
        
        return r2.text

    if bio_priv == "2":
        _log(f"Going to check '{username}' bio as follower")
        r2 = s2.get('/home') 
        csrf_token = re.search(r'<input id="csrf_token" name="csrf_token" type="hidden" value="(.*)">', r2.text).group(1)
        r2 = s2.post(f'/follow/{username}', data = {'token': token, 'csrf_token':csrf_token})
        try:
            r2 = s2.get(f"/user/{username}")
        except Exception as e:
            die(ExitStatus.DOWN, f"Failed to get {username} account: {e}")
        if r2.status_code != 200:
            die(ExitStatus.MUMBLE, f"Unexpected /user/{username} {r.status_code}")
       
        return r2.text
    
    if bio_priv == "3":
        _log(f"Going to check '{username}' bio as author")
        try:
            r = s.get(f"/user/{username}")
        except Exception as e:
            die(ExitStatus.DOWN, f"Failed to get {username} account: {e}")
        if r.status_code != 200:
            die(ExitStatus.MUMBLE, f"Unexpected /user/{username} {r.status_code}")
        
        soup = BeautifulSoup(r.text, 'html.parser')
        text  = [a.text for a in soup.find_all("div", class_ = "container")]
        
        return r.text
 
def gen_bio():
    r = RandomWords()
    bio = ""
    for i in range(random.randint(3,10)):
        bio += r.get_random_word() + " "
    return bio

def post_picture(s, flag):
    img = Image.new(mode="RGB", size=(700,100), color='white')
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype('arial.ttf', 28)                                                                                    
    draw.text((10, 10), flag, font=font, fill='black')
        
    img.save("123.png")
    
    r = s.get('/create-post') 
    csrf_token = re.search(r'<input id="csrf_token" name="csrf_token" type="hidden" value="(.*)">', r.text).group(1)

    try:
        with open('123.png', 'rb') as f:
            r = s.post("/create-post", 
                            files = {'picture': f}, 
                            data = dict(title= gen_title(), text = "...", csrf_token=csrf_token))
        post_id = re.search(r'<a href="/post/(.*)" class="btn btn-outline-secondary"> View post </a>', r.text).group(1)
    
    except Exception as e:
        die(ExitStatus.DOWN, f"Failed to upload image: {e}")
    if r.status_code != 200:
        die(ExitStatus.CORRUPT, f"Unexpected  /create-post code {r.status_code}")
    return post_id

def get_text_from_image(username, token, flag_id, host):
    s2 = FakeSession(host, PORT)
    username2, email2, password2 = create_user()
    token2 = sign_up(s2, username2, email2, password2)
    login(s2, username2, password2)

    r2 = s2.get('/home') 
    csrf_token = re.search(r'<input id="csrf_token" name="csrf_token" type="hidden" value="(.*)">', r2.text).group(1)
    r2= s2.post(f'/follow/{username}', data = {'token': token, 'csrf_token':csrf_token})

    r2 = s2.get(f"/post/{flag_id}")

    image_name = re.search(r'<img src=" /image/(.*)" >', r2.text).group(1)
    
    r2 = s2.get(f"/image/{image_name}")
    if r2.status_code == 200:
        with open("321.png", 'wb') as f:
            f.write(r2.content)
      
    text =  pytesseract.image_to_string('321.png')
    return text  

def put(hostname: str, flag: str, vuln: str):
    s = FakeSession(hostname, PORT)
    username, email, password = create_user()
    if vuln in '123456':
        token = sign_up(s, username, email, password)
        login(s, username, password)
    else:
        die(ExitStatus.DOWN,f'Checker error, Unexpected vuln value: {vuln}')

    #1. flag in "about me" accessible only for me
    if vuln == "1":
        create_bio(s, username, flag, "3")
        data = json.dumps({
        "username": username,
        "password": password
        })

        print(data, flush=True)  
        die(ExitStatus.OK, f"{data}")

    #2. flag in "about me" accessible for followers
    if vuln == "2":
        create_bio(s, username, flag, "2")
        data = json.dumps({
        "username": username,
        "token": token
        })

        print(data, flush=True)  
        die(ExitStatus.OK, f"{data}")

    #3. flag in text-post as text
    if vuln == "3":
        flag_post_id = post_text(s, flag)
        data = json.dumps({
        "flag_id": flag_post_id,
        "username": username,
        "token": token
        })

        print(data, flush=True)  
        die(ExitStatus.OK, f"{data}")

    #4. flag in text-post as brainfuck
    if vuln == "4":
        flag_brainfuck = string_to_bf(flag, False)
        flag_post_id = post_text(s, flag_brainfuck)
        data = json.dumps({
        "flag_id": flag_post_id,
        "username": username,
        "token": token
        })

        print(data, flush=True)  
        die(ExitStatus.OK, f"{data}")

    #5. flag in post as image
    if vuln == "5":
        
        flag_post_id = post_picture(s, flag)
        data = json.dumps({
        "flag_id": flag_post_id,
        "username": username,
        "token": token
        })
            
        print(data, flush=True)  
        die(ExitStatus.OK, f"{data}") 

def get(hostname, fid, flag, vuln):
    print("START GET")
    #'{"k1": "v1", "k2":"v2"}'
    try:     
        data = json.loads(fid)
        if not data:
            raise ValueError
    except:
        die(
            ExitStatus.CHECKER_ERROR,
            f"Unexpected flagID from jury: {fid}! Are u using non-RuCTF checksystem?",
        )
    
    if vuln not in '12345':   
        die(ExitStatus.DOWN,f'Checker error, Unexpected vuln value: {vuln}')

    s = FakeSession(hostname, PORT)
    if vuln == "1":
        username = data['username']
        password = data['password']
        login(s, username, password)
        if flag not in check_bio(s, username, "3"):
            die(ExitStatus.CORRUPT, f"Can't find a flag {username} in bio")  
        die(ExitStatus.OK, f"All OK! Successfully retrieved a flag from bio")

    if vuln == "2":
        username = data['username']
        token = data['token']
        if flag not in check_bio(s, username, "2", token, hostname):
            die(ExitStatus.CORRUPT, f"Can't find a flag {username} in bio")  
        die(ExitStatus.OK, f"All OK! Successfully retrieved a flag from bio")
    
    if vuln == "3":
        flag_id = data['flag_id']
        username = data['username']
        token = data['token']

        if flag not in get_post(username, token, flag_id, hostname):
            die(ExitStatus.CORRUPT, f"Can't find a flag {username} in posts")  
        die(ExitStatus.OK, f"All OK! Successfully retrieved a flag from posts")

    if vuln == "4":
        flag_id = data['flag_id']
        username = data['username']
        token = data['token']
        brainflag = string_to_bf(flag, False)

        if brainflag not in get_post(username, token, flag_id, hostname):
            die(ExitStatus.CORRUPT, f"Can't find a flag {username} in posts")  
        die(ExitStatus.OK, f"All OK! Successfully retrieved a flag from posts")
    
    if vuln == "5":
        flag_id = data['flag_id']
        username = data['username']
        token = data['token']
        if flag[:15] not in get_text_from_image(username, token, flag_id, hostname):
            die(ExitStatus.CORRUPT, f"Can't find a flag {username} in image post")  
        die(ExitStatus.OK, f"All OK! Successfully retrieved a flag from image post")

class FakeSession(requests.Session):
    """
    FakeSession reference:
        - `s = FakeSession(host, PORT)` -- creation
        - `s` mimics all standard request.Session API except of fe features:
            -- `url` can be started from "/path" and will be expanded to "http://{host}:{PORT}/path"
            -- for non-HTTP scheme use "https://{host}/path" template which will be expanded in the same manner
            -- `s` uses random browser-like User-Agents for every requests
            -- `s` closes connection after every request, so exploit get splitted among multiple TCP sessions
    Short requests reference:
        - `s.post(url, data={"arg": "value"})`          -- send request argument
        - `s.post(url, headers={"X-Boroda": "DA!"})`    -- send additional headers
        - `s.post(url, auth=(login, password)`          -- send basic http auth
        - `s.post(url, timeout=1.1)`                    -- send timeouted request
        - `s.request("CAT", url, data={"eat":"mice"})`  -- send custom-verb request
        (response data)
        - `r.text`/`r.json()`  -- text data // parsed json object
    """

    USER_AGENTS = [
        """Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/11.1 Safari/605.1.15""",
        """Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36""",
        """Mozilla/5.0 (Windows; U; Windows NT 6.1; rv:2.2) Gecko/20110201""",
        """Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10.6; en-US; rv:1.9.2.13; ) Gecko/20101203""",
        """Mozilla/5.0 (Windows NT 5.1) Gecko/20100101 Firefox/14.0 Opera/12.0""",
    ]
    def __init__(self, host, port):
        super(FakeSession, self).__init__()
        if port:
            self.host_port = "{}:{}".format(host, port)
        else:
            self.host_port = host

    def prepare_request(self, request):
        r = super(FakeSession, self).prepare_request(request)
        r.headers["User-Agent"] = random.choice(FakeSession.USER_AGENTS)
        r.headers["Connections"] = "close"
        return r

    def request(self, method, url,
                params=None, data=None, headers=None,
                cookies=None, files=None, auth=None, timeout=None, allow_redirects=True,
                proxies=None, hooks=None, stream=None, verify=None, cert=None, json=None,
                ):
        if url[0] == "/" and url[1] != "/":
            url = "http://"+self.host_port + url
        else:
            url = url.format(host=self.host_port)
        r = super(FakeSession, self).request(
            method, url, params, data, headers, cookies, files, auth, timeout,
            allow_redirects, proxies, hooks, stream, verify, cert, json,
        )
        if TRACE:
            print("[TRACE] {method} {url} {r.status_code}".format(**locals()))
        return r
                
def info():
    print("vulns: 3:3:1:2:2", flush=True, end="")
    exit(101)

def _log(obj):
    if DEBUG and obj:
        caller = inspect.stack()[1].function
        print(f"[{caller}] {obj}", file=sys.stderr)
    return obj

class ExitStatus(Enum):
    OK = 101
    CORRUPT = 102
    MUMBLE = 103
    DOWN = 104
    CHECKER_ERROR = 110

def die(code: ExitStatus, msg: str):
    if msg:
        print(msg, file=sys.stderr)
    exit(code.value)

def _main():
    try:
        cmd = argv[1]
        hostname = argv[2]
        if cmd =="get":
            fid, flag, vuln = argv[3:]
            get(hostname, fid, flag, vuln)
        elif cmd == "put":
            fid, flag, vuln = argv[3:]
            put(hostname, flag, vuln)
        elif cmd == "check":
            check(hostname)
        elif cmd == "info":
            info()
        else:
            raise IndexError
    except IndexError:
        die(ExitStatus.CHECKER_ERROR, f"Usage: {argv[0]} <check|get|put> [<hostname> [<id> <flag> <vuln>]]",)

if __name__ == "__main__":
    _main()