#!/usr/bin/env python
# -*- coding: utf-8 -*-
import urllib2
import config
import random
import codecs
import json
import re
import os
import requests
import sqlite3
import time
import sys
import logging

# ====================
# 工具函数
# ====================

HEADER = config.HEADER
TIMEOUT = config.TIMEOUT
ID = config.ID

def init_time(lt):
    # 0. init
    wait_sec = 999
    random_sec = 999
    time_str = ''

    # 1. random_sec
    random_sec = random.randint(0, 10) - 5

    # 2. wait_sec
    # print lt[3]
    if lt[3] in range(2, 9):
        wait_sec = 300
    elif lt[3] in range(9, 13):
        wait_sec = 60
    elif lt[3] in [21, 22, 23, 0, 1]:
        wait_sec = 20
    else: # [13, 21)点
        wait_sec = 30

    if lt[4] % 5 == 0:
        wait_sec += 60

    # 3. time_str
    time_str = '%d_%02d_%02d__%02d_%02d_%02d' % (lt[0], lt[1], lt[2], lt[3], lt[4], lt[5])

    return wait_sec + random_sec, time_str

# def sleep(i, step=10):
#     n = i
#     print 'sleep %ds...' % n
#     n -= step
#     if n > 0:
#         time.sleep(step)
#         sleep(n, step)
#     else:
#         time.sleep(i)

def sleep(sec, step=100):
    for i in range(sec):
        if i % step == 0:
            sys.stdout.write('sleep %d/%d s ...\r' % (i+1, sec))
            sys.stdout.flush()
        time.sleep(1)



def append_log(s):
    try:
        f_log = codecs.open('log/log.txt', 'a', 'utf-8')
        f_log.write(s)
    except IOError, e:
        print u'append_log 出错：'
        print e
    finally:
        if f_log:
            f_log.close()

def appendUserInfoToDb(id, timestr, isUpdated, title, json=''):
    if isUpdated:
        isUpdated = 1
    else:
        isUpdated = 0
    # 连接数据库
    conn = sqlite3.connect('log/%s.db' % id)
    cursor = conn.cursor()
    try:
        cursor.execute("insert into t1 (timestr, is_updated, title, json) values (?,?,?,?)",
            (timestr, isUpdated, title, json)
        )
    finally:
        cursor.close()
        conn.commit()
        conn.close()

def appendLikesToDb(id, timestr, isLikesNumUpdated, likesNumOld, likesNum):
    if isLikesNumUpdated:
        isLikesNumUpdated = 1
    else:
        isLikesNumUpdated = 0
    # 连接数据库
    conn = sqlite3.connect('log/%s.db' % id)
    cursor = conn.cursor()
    try:
        cursor.execute('select id, timestr from t1 where timestr=?', (timestr,))
        rArr = cursor.fetchall()
        # print rArr
        if len(rArr) > 0:
            # timestr 存在
            # print 'cunzai'
            cursor.execute('update t1 set is_likes_num_updated=?, likes_num_old=?, likes_num=? where timestr=?',
                           (isLikesNumUpdated, likesNumOld, likesNum, timestr)
            )
        else:
            # timestr 不存在
            # print 'bucunzai'
            cursor.execute("insert into t1 (timestr, is_likes_num_updated, likes_num_old, likes_num) values (?,?,?,?)",
                (timestr, isLikesNumUpdated, likesNumOld, likesNum)
            )
    finally:
        cursor.close()
        conn.commit()
        conn.close()

def appendMemoToDb(id, timestr, memo):
    # 连接数据库
    conn = sqlite3.connect('log/%s.db' % id)
    cursor = conn.cursor()
    try:
        cursor.execute('select id, timestr from t1 where timestr=?', (timestr,))
        rArr = cursor.fetchall()
        # print rArr
        if len(rArr) > 0:
            # timestr 存在
            # print 'cunzai'
            cursor.execute('update t1 set memo=? where timestr=?',
                           (memo, timestr)
            )
        else:
            # timestr 不存在, 一般不可能出现这种情况
            # print 'bucunzai'
            cursor.execute("insert into t1 (timestr, memo) values (?,?)",
                (timestr, memo)
            )
    finally:
        cursor.close()
        conn.commit()
        conn.close()

def trimDb(configId):
    # 连接数据库
    conn = sqlite3.connect('log/%s.db' % configId)
    cursor = conn.cursor()
    try:
        cursor.execute('''delete from t1
            where title like 'not modified%'
            and is_likes_num_updated = 0
            and memo is null
        ''')
        print 'trimDb: deleted', cursor.rowcount, 'rows...'
    finally:
        cursor.close()
        conn.commit()
        conn.close()

def trimDbDeeply(configId):
    # 浅删除
    trimDb(configId)

    # 深删除
    # 连接数据库
    conn = sqlite3.connect('log/%s.db' % configId)
    cursor = conn.cursor()
    try:
        cursor.execute('''delete from t1
        where (title like 'json not completed%' or title like '%re run main%')
        and is_likes_num_updated = 0
        and memo is null;
        ''')
        print 'trimDbDeeply: deleted', cursor.rowcount, 'rows...'

    finally:
        cursor.close()
        conn.commit()
        conn.close()

def _save_img_once(img_url, path):
    try:
        # request = urllib2.Request(img_url, headers=HEADER)
        # response = urllib2.urlopen(request, timeout=IMG_TIMEOUT)
        # img_data = response.read()
        img_data = requests.get(img_url,
                                timeout=config.IMG_TIMEOUT_TUPLE,
                                headers=config.HEADER
                                ).content

        f = file(path, "wb")
        f.write(img_data)
        f.close()
        return True
    except urllib2.URLError, e:
        if hasattr(e,"code"):
            print '_save_img_once: e.code:'
            print e.code
        if hasattr(e,"reason"):
            print '_save_img_once: e.reason'
            print e.reason
        return False

def save_img(img_url, path):
    r = _save_img_once(img_url, path)
    if not r:
        print 'save_img: retry save img'
        _save_img_once(img_url, path)

def dump_obj_to_file(obj, path):
    f = codecs.open(path, 'w', 'utf-8')
    json.dump(obj, f, ensure_ascii=False, indent=4)
    f.close()

def write_txt_to_file(txt, path, encoding='utf-8'):
    f = codecs.open(path, 'w', encoding)
    f.write(txt)
    f.close()


def get_user_info_old():
    try:
        f_in = open('temp/user_info_old.json', 'r')
        user_info_old = json.load(f_in)
        f_in.close()
    except IOError, e:
        # 没有temp/user_info_old.json
        user_info_old = get_user_info()

        f_in = codecs.open('temp/user_info_old.json', 'w', 'utf-8')
        json.dump(user_info_old, f_in, ensure_ascii=False, indent=4)
        f_in.close()

    finally:
        if f_in:
            f_in.close()
        return user_info_old

def get_user_info():
    user_info = {}
    try: 
        request = urllib2.Request(config.MAIN_URL, headers=config.HEADER)
        response = urllib2.urlopen(request, timeout=config.TIMEOUT)
        res_txt = response.read()
        response_dict = json.loads(res_txt) 
        user_info = response_dict.get('userInfo')
        return user_info
    except urllib2.URLError, e:
        if hasattr(e,"code"):
            print e.code
        if hasattr(e,"reason"):
            print e.reason
    finally:
        return user_info

def write_user_info_to_json(userInfo, timeStr):
    # 更新old，以备下次对比
    dump_obj_to_file(userInfo, 'temp/user_info_old.json')
    dump_obj_to_file(userInfo, 'log/%s__user_info.json' % timeStr)

    new_dict = {}
    new_dict[u'时间'] = timeStr
    new_dict[u'头像'] = userInfo.get('profile_image_url')
    new_dict[u'背景图'] = userInfo.get('cover_image_phone')
    new_dict[u'昵称'] = userInfo.get('screen_name')
    new_dict[u'签名'] = userInfo.get('description')
    new_dict[u'关注'] = userInfo.get('follow_count')
    new_dict[u'粉丝'] = userInfo.get('followers_count')
    new_dict[u'微博数'] = userInfo.get('statuses_count')
    
    dump_obj_to_file(new_dict, 'log/%s__user_info_filted.json' % timeStr)



# ====================
# email
# ====================
from email import encoders
from email.header import Header
from email.mime.text import MIMEText
from email.utils import parseaddr, formataddr
import smtplib
from email.mime.multipart import MIMEMultipart

FROM_ADDR = config.FROM_ADDR
PASSWORD = config.PASSWORD
TO_ADDR = config.TO_ADDR
SMTP_SERVER = config.SMTP_SERVER

def _format_addr(s):
    name, addr = parseaddr(s)
    return formataddr(( \
        Header(name, 'utf-8').encode(), \
        addr.encode('utf-8') if isinstance(addr, unicode) else addr))

def sendEmail(msgStr, subject=ID):

    def main(msgStr, subject):
        msg = MIMEText(msgStr, 'plain', 'utf-8')
        msg['From'] = _format_addr(u'python <%s>' % FROM_ADDR)
        msg['To'] = _format_addr(u'zk <%s>' % TO_ADDR)
        msg['Subject'] = Header(subject, 'utf-8').encode()

        server = smtplib.SMTP(SMTP_SERVER, 25)
        # server.set_debuglevel(1)
        server.login(FROM_ADDR, PASSWORD)
        server.sendmail(FROM_ADDR, [TO_ADDR], msg.as_string())
        server.quit()

    main(msgStr, subject)

def sendHtmlEmailFromDict(d, subject=ID):
    htmlStr = ''
    for i in d:
        ul = ''
        for j in i:
            ul += '<li>%s</li>' % j
        ul = '<ul>%s</ul>' % ul
        htmlStr += ul

    msg = MIMEText(htmlStr, 'html', 'utf-8')
    msg['From'] = _format_addr(u'python <%s>' % FROM_ADDR)
    msg['To'] = _format_addr(u'zk <%s>' % TO_ADDR)
    msg['Subject'] = Header(subject, 'utf-8').encode()

    server = smtplib.SMTP(SMTP_SERVER, 25)
    # server.set_debuglevel(1)
    server.login(FROM_ADDR, PASSWORD)
    server.sendmail(FROM_ADDR, [TO_ADDR], msg.as_string())
    server.quit()

# 添加附件
def _attachFile(msgObj, file, index):
    # 构造附件1，传送当前目录下的 test.txt 文件
    att1 = MIMEText(open(file, 'rb').read(), 'base64', 'utf-8')
    att1["Content-Type"] = 'application/octet-stream'
    # 这里的filename可以任意写，写什么名字，邮件中显示什么名字
    att1["Content-Disposition"] = 'attachment; filename="content%03d.txt"' % (index + 1)
    msgObj.attach(att1)

def sendEmailWithFileLst(msgStr='', fileLst=[], subject=u'%s 附件' % ID):

    # 创建一个带附件的实例
    msgObj = MIMEMultipart()
    msgObj['From'] = _format_addr(u'python <%s>' % FROM_ADDR)
    msgObj['To'] = _format_addr(u'zk <%s>' % TO_ADDR)
    msgObj['Subject'] = Header(subject, 'utf-8').encode()

    # 邮件正文内容
    htmlStr = '<p>%s</p>' % msgStr
    msgObj.attach(MIMEText(htmlStr, 'html', 'utf-8'))

    # 添加附件
    for index in range(len(fileLst)):
        file = fileLst[index]
        _attachFile(msgObj, file, index)

    # 发送
    server = smtplib.SMTP(SMTP_SERVER, 25)
    # server.set_debuglevel(1)
    server.login(FROM_ADDR, PASSWORD)
    server.sendmail(FROM_ADDR, [TO_ADDR], msgObj.as_string())
    server.quit()

# ===============================
# filt
# ===============================

# filt 'mblog'
def _filtMblog(mblog):

    # 删除不需要的key
    keysToDel = ['textLength', 'thumbnail_pic', 'bmiddle_pic', 'buttons', 'visible',
                 'favorited', 'id', 'bid', 'isLongText', 'page_info', 'pid', 'cardid',
                 'picStatus', 'sync_mblog', 'is_imported_topic', 'topic_id', 'favorited',
                 'isLongText', 'favorited', 'expire_time'
                 ]
    for k in keysToDel:
        if mblog.get(k) != None:
            del mblog[k]
    # 不能这样写
    # for k in mblog:
    #     if k in keysToDel:
    #         del mblog[k]


    # 修改属性 'pics', 'user'
    if mblog.get('pics'):
        mblog['pics'] = len(mblog['pics'])
    if mblog.get('user'):
        mblog['user'] = mblog['user']['screen_name']

    if mblog.has_key('retweeted_status'):
        _filtMblog(mblog.get('retweeted_status'))

# filt 'cards'
def filtCards(cardLst):
    # 取出嵌套的卡片, 重构cardLst
    for i, card in enumerate(cardLst):
        # 这是一个卡片组
        if card.get('card_type') == 11:
            if card.get('itemid') == "INTEREST_PEOPLE":
                continue

            length = len(card.get('card_group'))

            if length == 1:
                # 里边有一个普通微博卡片
                if card.get('card_group')[0].get('card_type') == 9:
                    cardLst[i] = card.get('card_group')[0]

            elif length == 2:
                # 里边有两个卡片，第二个是文章卡片
                if card.get('card_group')[1].get('card_type') == 8:
                    cardLst[i] = card.get('card_group')[1]
                # 里边有两个卡片，第二个未知
                else:
                    cardLst[i] = card.get('card_group')[1]
            else:
                # 未知情况，取最后一个卡片
                cardLst[i] = card.get('card_group')[length-1]


    # 提取 mblog, 重构
    for i in range(len(cardLst)):
        if cardLst[i].get('card_type') == 9:
            cardLst[i] = cardLst[i].get('mblog')

    for i in range(len(cardLst)):
        if not cardLst[i]:
            print 'cardLst[%d] is None' % i
            time.sleep(500)
            break
        _filtMblog(cardLst[i])

def renameFiltedCards(cardLst):
    def _rename(card):
        for enK, chK in renameDict.items():
            if card.get(enK) != None:
                card[chK] = card.get(enK)
                del card[enK]


    renameDict = {
        "reposts_count": u"转发数",
        "original_pic": u"原图链接",
        "text": u"文字​",
        "created_at": u"创建于",
        "source": u"来自",
        "attitudes_count": u"点赞数",
        "comments_count": u"评论数",
        "user": u"用户",
        "pics": u"图片"
    }
    newCardLst = []
    for card in cardLst:
        _rename(card)
        for k in card:
            if k == 'retweeted_status':
                _rename(card.get('retweeted_status'))



