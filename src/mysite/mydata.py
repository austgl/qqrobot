# -*- coding: utf-8 -*-
#kv key：原始qq            值：score
#   key：原始qq+'state'    值：学习状态
#   key：原始qq+'qiubai'   值：糗百等第
#   key: 'have'+qq         值：有无好友
#   key: qq+'over'         值：今日消费完毕
#memcache  key：str(int)     值：对应糗百
#          key：原始qq+'q'   值：状态问题
#__author__ = www.skyduy.com
import MySQLdb, random, time
import pylibmc as memcache
from qiubai import qiubai

from django.http import HttpResponse
from sae.const import (MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASS, MYSQL_DB)
import sae.kvdb

import sys
reload(sys)
sys.setdefaultencoding('utf8')

Specialstate = ('学习 ', '帮助 ', '段子 ', '我的豆子 ')

def maildata():
    qqmail = 'your mail'
    psw = 'your password'
    return qqmail,psw

#下面函数调用之前记得先创建数据库(具体表和字段函数中有提及)
def getmaster():
    mc = memcache.Client()
    if not mc.get('qq') or not mc.get('psw'):
        cxn = MySQLdb.connect(
            host  = MYSQL_HOST,
            port  = int(MYSQL_PORT),
            user  = MYSQL_USER,
            passwd = MYSQL_PASS,
            db = MYSQL_DB,
            charset = 'utf8')
        cur = cxn.cursor()
        cur.execute('''SELECT * FROM user_data ''')
        data = cur.fetchall()[0]
        cur.close()
        cxn.commit()
        mc.set("qq", data[0], 64800)
        mc.set("psw", data[1], 64800)
    qq = mc.get('qq')
    psw = mc.get('psw')
    data = (qq,psw)
    return data

def putfriends(who):
    who = who.encode("utf-8")
    kv = sae.kvdb.KVClient()
    havewho = 'have'+who
    if kv.get(havewho):
        kv.disconnect_all()
        return
    kv.set(havewho, True)
    kv.disconnect_all()
    cxn = MySQLdb.connect(
        host  = MYSQL_HOST,
        port  = int(MYSQL_PORT),
        user  = MYSQL_USER,
        passwd = MYSQL_PASS,
        db = MYSQL_DB,
        charset = 'utf8')
    cur = cxn.cursor()
    try:
        cur.execute("INSERT INTO friends (qq) VALUES(%s)",(who))
    except Exception:
        pass
    cur.close()
    cxn.commit()
    return

def Summary(who,num,flag):
    if flag < 0:
        rank = num
        kv = sae.kvdb.KVClient()
        qq = who.encode("utf-8")
        whoover = qq+'over'
        whoqiubai = who+'qiubai'
        if not kv.get(qq) and kv.get(qq)!= 0:
            kv.set(qq, 20)
        score = kv.get(qq)
        if not kv.get(whoover):
            kv.set(whoover, 0)
        over = kv.get(whoover)
        if rank >= 11 and rank <= 20:
            less = 1
        elif rank >= 6 and rank <= 10:
            less = 2
        elif rank >= 3 and rank <= 5:
            less = 4
        else:
            less = 8
        if over == 0:
            if score >= less:
                remain = score-less
                kv.set(qq,remain)
                if rank > 1:
                    content2 =  '\n[TIP: 你购买了价值%s豆的段子，还剩下%s颗豆子]'%(less, remain)
                    kv.set(whoqiubai, rank-1)
                else:
                    kv.set(whoover,1)
                    content2 =  '\n[TIP: 你购买了价值%s豆的最后一餐段子，还剩下%s颗豆子]'%(less, remain)
                    kv.set(whoqiubai, 20)
                mc = memcache.Client()
                if not mc.get(str(rank-1)):
                    cxn = MySQLdb.connect(
                        host  = MYSQL_HOST,
                        port  = int(MYSQL_PORT),
                        user  = MYSQL_USER,
                        passwd = MYSQL_PASS,
                        db = MYSQL_DB,
                        charset = 'utf8')
                    cur = cxn.cursor()
                    cur.execute("SELECT * FROM qiubai ORDER BY addtime DESC limit 20")
                    all = cur.fetchall()
                    for i in range(20):
                        each = all[19-i][0].encode("utf-8")
                        mc.set(str(i), each, 86400)
                content1 = mc.get(str(rank-1))
                content = ('今日段子[%s]:\n'%(rank))+ content1+content2
                kv.disconnect_all()
                return content
            else:
                remain = score
                content = "你只有%s个豆子了,不够购买价值%s的段子，了快教教我吧，能赚豆子哦！"%(remain,less)
                kv.disconnect_all()
                return content
        else:
            if rank > 1:
                kv.set(whoqiubai, rank-1)
            else:
                kv.set(whoqiubai, 20)
            content2 = '\n[TIP:您已经看完了今日段子，段子于23:30更新，本条段子不消耗豆子. ]'
            mc = memcache.Client()
            if not mc.get(str(rank-1)):
                cxn = MySQLdb.connect(
                    host  = MYSQL_HOST,
                    port  = int(MYSQL_PORT),
                    user  = MYSQL_USER,
                    passwd = MYSQL_PASS,
                    db = MYSQL_DB,
                    charset = 'utf8')
                cur = cxn.cursor()
                cur.execute("SELECT * FROM qiubai ORDER BY addtime DESC limit 20")
                all = cur.fetchall()
                for i in range(20):
                    each = all[19-i][0].encode("utf-8")
                    mc.set(str(i), each, 86400)
            content1 = mc.get(str(rank-1))
            content = ('今日段子[%s]:\n'%(rank))+ content1+content2
            kv.disconnect_all()
            return content

    if flag>0:
        plus = num
        qq = who.encode("utf-8")
        kv = sae.kvdb.KVClient()
        if not kv.get(qq):
            kv.set(qq,20+plus)
        else:
            score = kv.get(qq)
            kv.set(qq,score+plus)
        kv.disconnect_all()

def showscore(who):
    qq = who.encode("utf-8")
    kv = sae.kvdb.KVClient()
    if not kv.get(qq) and kv.get(qq)!= 0:
        kv.set(qq,20)
    score = kv.get(qq)
    return score

def getback(who, QaT, state):
    if state == None:
        print 1
        if QaT[0] in Specialstate or QaT[0].endswith('把您加入他的好友列表'):
            if QaT[0] == '学习 ':
                who = who.encode("utf-8")
                whostate = who+'state'
                kv = sae.kvdb.KVClient()
                kv.set(whostate, 1)
                kv.disconnect_all()
                return ('啊...要学习了！请问我问题吧')
            elif QaT[0] == '帮助 ':
                content = '''小D指令如下:
1、'任何消息'(加1豆子/次) 可和小D聊天.
2、'学习'(加5豆子/次) 可教小D知识.
3、'段子'(减1~8豆子/次) 可讲糗事~[:copyright:糗事百科].
4、'我的豆子' 可查看豆子的剩余量.
5、'帮助' 再次获得本帮助信息
-----------------------------------
小D正在强化中,若发现BUG或有好的意见/建议,欢迎查看个人说明\
并提交信息,小D会赠予300豆子哦~'''
                return content
            elif QaT[0] == '段子 ':
                who = who.encode("utf-8")
                whoqiubai = who+'qiubai'
                kv = sae.kvdb.KVClient()
                if kv.get(whoqiubai):
                    num =  kv.get(whoqiubai)
                else:
                    num = 20
                kv.disconnect_all()
                content = Summary(who,num,flag = -1)
                return content
            elif QaT[0] == '我的豆子 ':
                count = showscore(who)
                content = '你还有%s颗豆子~请合理消费哦！'%count
                return content
            elif QaT[0].endswith('把您加入他的好友列表'):
                content = '''你好，欢迎添加小D为好友！
目前小D有三项技能哦~：
1、陪你聊天(直接发消息,每次+1豆子)
2、听你上课(回复'学习',每次+5豆子)
3、给你讲段子~(回复'段子',消耗豆子)[:copyright:糗事百科]
回复'帮助'可查看所有指令.
'''
                return content
            else:
                return ('该功能还没开启啊...')
        else:
            cxn = MySQLdb.connect(
                host  = MYSQL_HOST,
                port  = int(MYSQL_PORT),
                user  = MYSQL_USER,
                passwd = MYSQL_PASS,
                db = MYSQL_DB,
                charset = 'utf8')
            cur = cxn.cursor()
            cur.execute("SELECT COUNT(*) FROM learned WHERE question = %s",QaT[0])
            count = cur.fetchall()[0]
            if count[0] == 0:
                cur.close()
                cxn.commit()
                Summary(who,1,flag = 1)
                return 0
            else:
                #这里耗费豆子多的多，被教的问题越多，这里就越耗豆子
                cur.execute("SELECT * FROM learned WHERE question = %s",QaT[0])
                all = cur.fetchall()
                cur.close()
                cxn.commit()
                rand = random.randint(0,count[0]-1)
                Summary(who,1,flag = 1)
                return (all[rand][2])
    if state == 1:
        print 2
        if QaT[0] in Specialstate:
            return ('呀！这是命令我的指令！小D不能学习啊...换个问题重新问吧！')
        else:
            who = who.encode("utf-8")
            whostate = who+'state'
            kv = sae.kvdb.KVClient()
            kv.set(whostate, 2)
            kv.disconnect_all()

            mc = memcache.Client()
            whoq = who + 'q'
            mc.set(whoq, QaT[0], 3600)

            return ('唔...小D记住问题了，请给我答案吧！')
    if state == 2:
        print 3
        who = who.encode("utf-8")
        whostate = who+'state'
        kv = sae.kvdb.KVClient()
        kv.set(whostate, None)
        kv.disconnect_all()

        mc = memcache.Client()
        whoq = who + 'q'
        if not mc.get(whoq):
            return ('呜...小D只知道你在一小时或者更久之前问过问题，但是忘记问题\
            是什么了...')
        else:
            q = mc.get(whoq)
            a = QaT[0]
            learned(who,q,a)
            content =( '\(^o^)/YES！\n问题：%s\n答案：%s\nGot it!'%(q,a))
            mc.delete(whoq)
            Summary(who,5,flag = 1)
            return (content)

def putcontent(who,CaT,back):
    cxn = MySQLdb.connect(
        host  = MYSQL_HOST,
        port  = int(MYSQL_PORT),
        user  = MYSQL_USER,
        passwd = MYSQL_PASS,
        db = MYSQL_DB,
        charset = 'utf8')
    cur = cxn.cursor()
    cur.execute("INSERT INTO chat_record (the_qq,come_content,back_content,come_time) \
        VALUES(%s,%s,%s,%s)",(who,CaT[0],back,CaT[1]))
    cur.close()
    cxn.commit()
    return

def getstate(who):
    who = who.encode("utf-8")
    whostate = who+'state'
    kv = sae.kvdb.KVClient()
    if kv.get(whostate):
        state =  kv.get(whostate)
        kv.disconnect_all()
        return state
    else:
        return None

def learned(who,q,a):
    cxn = MySQLdb.connect(
        host  = MYSQL_HOST,
        port  = int(MYSQL_PORT),
        user  = MYSQL_USER,
        passwd = MYSQL_PASS,
        db = MYSQL_DB,
        charset = 'utf8')
    cur = cxn.cursor()
    try:
        cur.execute("INSERT INTO learned VALUES(%s,%s,%s)",(who,q,a))
    except Exception:
        pass
    cur.close()
    cxn.commit()

def Updating(request):
    #1 糗百更新至数据库
    all = qiubai()
    cxn = MySQLdb.connect(
        host  = MYSQL_HOST,
        port  = int(MYSQL_PORT),
        user  = MYSQL_USER,
        passwd = MYSQL_PASS,
        db = MYSQL_DB,
        charset = 'utf8')
    cur = cxn.cursor()
    try:
        for i in range(20):
            each = all[i].encode("utf-8")
            cur.execute("INSERT INTO qiubai (content) VALUES(%s)",(each))
    except Exception:
        pass
    cur.close()
    cxn.commit()

    #2 糗百更新至memcache
    mc = memcache.Client()
    for i in range(20):
        each = all[i].encode("utf-8")
        mc.set(str(i), each, 86400)

    #3 分数写入数据库之前，将昨日数据库备份
    cxn = MySQLdb.connect(
        host  = MYSQL_HOST,
        port  = int(MYSQL_PORT),
        user  = MYSQL_USER,
        passwd = MYSQL_PASS,
        db = MYSQL_DB,
        charset = 'utf8')
    cur = cxn.cursor()
    #备份
    cur.execute("DROP table bcfriends")
    cur.execute("CREATE table bcfriends select * from friends")

    #更新
    #利用这个风险有点大...唉，别初始化就行了
    #将分数写入数据库
    cur.execute("SELECT COUNT(*) FROM friends")
    count = cur.fetchall()[0][0]
    cur.execute("SELECT * FROM friends")
    all = cur.fetchall()
    kv = sae.kvdb.KVClient()
    for i in range(count):
        qq = all[i][0].encode("utf-8")
        if not kv.get(qq):
            score = 20
            kv.set(qq, score)
        else:
            score = kv.get(qq)
        cur.execute("UPDATE friends SET score=%s WHERE qq=%s",(score,qq))
        time.sleep(0.5)
    kv.disconnect_all()
    cur.close()
    cxn.commit()

    #4 num归20
    kv = sae.kvdb.KVClient()
    for i in range(count):
        qq = all[i][0].encode("utf-8")
        whoqiubai = qq+'qiubai'
        kv.set(whoqiubai, 20)
    kv.disconnect_all()

    #5、who over归0
    kv = sae.kvdb.KVClient()
    for i in range(count):
        qq = all[i][0].encode("utf-8")
        whoover = qq+'over'
        kv.set(whoover, 0)
    kv.disconnect_all()


    # 将备份数据导入kv,
    # cxn = MySQLdb.connect(
    #     host  = MYSQL_HOST,
    #     port  = int(MYSQL_PORT),
    #     user  = MYSQL_USER,
    #     passwd = MYSQL_PASS,
    #     db = MYSQL_DB,
    #     charset = 'utf8')
    # cur = cxn.cursor()
    # cur.execute("SELECT COUNT(*) FROM friends")
    # count = cur.fetchall()[0][0]
    # cur.execute("SELECT * FROM friends")
    # all = cur.fetchall()
    # cur.close()
    # cxn.commit()
    # kv = sae.kvdb.KVClient()
    # for i in range(count):
    #     qq = all[i][0].encode("utf-8")
    #     score = all[i][1]
    #     kv.set(qq, score)
    # kv.disconnect_all()

    return HttpResponse('update ok')
