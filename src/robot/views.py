# -*- coding: utf-8 -*-
#__author__='luffy@skyduy.com' Inspired by ihc
#__author__= 'http://www.skyduy.com'

import urllib, urllib2, cookielib
import re, time

from mysite.mydata import getmaster, putfriends, putcontent, getback, getstate, maildata

import pylibmc as memcache
from sae.taskqueue import Task, TaskQueue
from sae.mail import EmailMessage
from sae.taskqueue import Task, TaskQueue

from django.http import HttpResponse, HttpResponseRedirect, HttpRequest
from django.shortcuts import render_to_response

import sys
reload(sys)
sys.setdefaultencoding('utf8')



def get(URL,back = 1):
    ua='Mozilla/5.0 (Linux; U; Android 2.2; en-us; Nexus One Build/FRF91) AppleWebKit/533.1 (KHTML, like Gecko) Version/4.0 Mobile Safari/533.1'
    cookie=cookielib.CookieJar()
    opener=urllib2.build_opener(urllib2.HTTPCookieProcessor(cookie))
    opener.addheaders = [('User-Agent', ua)]
    urllib2.install_opener(opener)
    if back:
        return urllib2.urlopen(URL).read()
    else:
        urllib2.urlopen(URL)

def post(URL,data):
    ua='Mozilla/5.0 (Linux; U; Android 2.2; en-us; Nexus One Build/FRF91) AppleWebKit/533.1 (KHTML, like Gecko) Version/4.0 Mobile Safari/533.1'
    cookie=cookielib.CookieJar()
    opener=urllib2.build_opener(urllib2.HTTPCookieProcessor(cookie))
    opener.addheaders = [('User-Agent', ua)]
    urllib2.install_opener(opener)
    req = urllib2.Request(URL, data)
    return urllib2.urlopen(req).read()

def givesid(flag,html):
    if flag == 0:
        pass
    else:
        From2 = re.compile(r'sid=(.+?)&amp;aid=nqqchatMain">手动刷新')
        me2 = From2.search(html)
        sid = me2.group(1).decode('utf-8')
        mc = memcache.Client()
        if not mc.get('sid'):
            mc.set("sid", sid, 64800)
        else:
            mc.replace("sid", sid, 64800)

def getsid():
    mc = memcache.Client()
    if not mc.get('sid'):
        return 0
    else:
        return mc.get('sid')

def login():
    (qq,psw) = getmaster()
    URL ='http://pt.3g.qq.com/s?aid=nLogin3gqq'
    html = get(URL)
    
    From = re.compile(r'<br /><FORM action="(.+?)"')
    me1 = From.search(html)
    LOGIN_URL = me1.group(1).decode('utf-8')

    postdata=urllib.urlencode({
        'qq':qq,
        'pwd':psw,
        'bid_code':'3GQQ',
        'toQQchat':'true',
        'login_url':'http://pt.3g.qq.com/s?aid=nLoginnew&amp;q_from=3GQQ',
        'q_from':'',
        'modifySKey':'0',
        'lloginType':'1',
        'aid':'nLoginHandle',
        'i_p_w':'qq|pwd|'
    })
    html = post(LOGIN_URL,postdata)
    try:
        From2 = re.compile(r'sid=(.+?)&amp;aid=nqqchatMain">手动刷新')
        me2 = From2.search(html)
        sid = me2.group(1).decode('utf-8')
        flag = 0
    except Exception:
        From2 = re.compile(r'handleLogin\?sid=(.+?)&amp;vdata="')
        me2 = From2.search(html)
        sid = me2.group(1).decode('utf-8')
        flag = 1
    return sid,html,flag

def getdata(ihc1,ihc2,ihc3):
    a = []
    while True:
        istart = ihc1.find(ihc2)+ len(ihc2)
        if ihc1.find(ihc2)==-1:
            return a
        iend = ihc1.find(ihc3, istart)
        if iend==-1:
            return a
        a.append(ihc1[istart:iend])
        ihc1 = ihc1[iend+len(ihc3):-1]
    return a

def newchat(html):
    content = '咕......小D不知道怎么回答了...请教给小D吧！（利用指令“学习”）'
    From = re.compile(r'u=(.+?)&amp;on')
    me = From.search(html)
    he = me.group(1).decode('utf-8')
    putfriends(he)
    a = 'bm-blue">'
    b = '<div class="bg'
    the_block = getdata(html,a,b)
    c = '<p>'
    d = '</p>'
    the_message = getdata(the_block[0],c,d)
    e = '&nbsp;'
    the_time = getdata(the_block[0],e,d)
    temp = []
    for i in range(len(the_message)):
        temp.append((the_message[i],the_time[i]))
    for each in temp:
        state = getstate(he)
        back = getback(he,temp[0],state)
        if back != 0:
            content = back
        sid = getsid()
        sendurl = 'http://q32.3g.qq.com/g/s?sid='+sid
        postdata=urllib.urlencode({
            'msg': content,
            'u': he,
            'do': 'send',
            'on': '1',
            'saveURL': '0',
            'aid': '发送',
        })
        post(sendurl,postdata)
        putcontent(he,each,content)
        time.sleep(0.5)

def refresh(request):
    flag = 0
    sid = getsid()
    if sid == 0:
        return HttpResponse('cann\'t get sid',status=521)
    reurl = 'http://q16.3g.qq.com/g/s?sid='+sid+'&aid=nqqchatMain'
    html = get(reurl)
    From = re.compile(r'sid=(.+?)&amp;aid=nqqchatMain">手动刷新')
    me = From.search(html)
    try:
        newsid = me.group(1).decode('utf-8')
    except Exception:
        time.sleep(10)
        return HttpResponse('sth wrong,refresh conn\'t work,may after some time, it\'s ok.', status=521)
    if newsid == sid:
        pass
    else:
        mc = memcache.Client()
        mc.replace("key", newsid, 64800)
        sid = newsid
    From1 = re.compile(r'alt="聊天"/>(.+?)</a>')
    me1 = From1.search(html)
    info = me1.group(1).decode('utf-8')
    if info != 'QQ':
        (qq,psw) = getmaster()
        chaturl = 'http://q16.3g.qq.com/g/s?sid='+sid+'&3G_UIN='+qq+'&saveURL=0&aid=nqqChat'
        html1 = get(chaturl)
        newchat(html1)
    else:
        flag = 1
    if flag == 0:
        time.sleep(6)
    else:
        time.sleep(7)
    return HttpResponse('ok')

def getverify(html):
    From2 = re.compile(r'src="(.+?)\.gif\?r=')
    me2 = From2.search(html)
    Extend = me2.group(1).decode('utf-8')

    r_sid1 = getdata(html,'name="r_sid" value="','"')
    r_sid = r_sid1[0]

    rip1 = getdata(html,'name="rip" value="','"')
    rip = rip1[0]

    url = getdata(html,'<img src="','"')
    URL = url[0]

    return Extend,r_sid,rip,URL

def main(request):
    sid, html, flag = login()
    if flag == 0:
        mc = memcache.Client()
        if not mc.get('sid'):
            mc.set("sid", sid, 64800)
        else:
            mc.replace("sid", sid, 64800)
        givesid(flag,'')
        return HttpResponse('login ok')
    else:
        Extend,r_sid,rip,URL = getverify(html)
        html =  render_to_response('verify.html', {'Extend': Extend,'r_sid':r_sid,'rip':rip, 'URL':URL})
        sendmail(html)
        return HttpResponse('mail has sent')

def main2(request):
     if request.method == 'GET':
         pass
     else:
        (qq,psw) = getmaster()
        extend = request.POST['extend']
        r_sid = request.POST['r_sid']
        rip = request.POST['rip']
        verify = request.POST['verify']
        sid = getsid()
        while sid == 0:
            time.sleep(1)
            sid = getsid()
        postdata=urllib.urlencode({
            'qq':qq,
            'u_token':qq,
            'hexpwd':'4A4962616E313233',
            'sid':sid,
            'hexp':'true',
            'nopre':'',
            'auto':'0',
            'loginTitle':'手机腾讯网',
            'q_from':'',
            'modifySKey':'0',
            'q_status':'20',
            'r':'44132',
            'loginType':'3',
            'login_url':'http://pt.3g.qq.com/s?aid=nLoginnew&amp;q_from=3GQQ',
            'extend':extend,
            'r_sid':r_sid,
            'bid_code':'3GQQ',
            'bid':'0',
            'toQQchat':'true',
            'rip':rip,
            'verify':verify,
            'submitlogin':'马上登录',
        })
        href = 'http://pt.3g.qq.com/handleLogin?sid='+sid+'&vdata=6C05F005DAD1CC5C129CDB1D1AAC6414'
        html = post(href,postdata)
        givesid(1,html)
        return HttpResponse(html)

def TASK(request):
    queue = TaskQueue('refresh')
    counts = queue.size()
    if counts<=150:
        for i in range(100):
            queue.add(Task("/refresh/"))
        content = str(counts) + '+100 ok'
    else:
        content = str(counts)+ 'needn\'t add'
    return HttpResponse(content)

def sendmail(html):
    m = EmailMessage()
    m.to = '收件人'
    m.subject = '收件主题'
    m.html = str(html)
    mail,psw = maildata()
    m.smtp = ('smtp.gmail.com', 587, mail, psw, True)
    m.send()

