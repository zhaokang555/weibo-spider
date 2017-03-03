#!/usr/bin/env python
# -*- coding: utf-8 -*-

import urllib
import urllib2
import json
import codecs
import time
import os
import utils
import config
import config2
import likes
import logging

URL = config.MAIN_URL
HEADER = config.HEADER
ID = config.ID
MAX_URGENT_LEVEL = config2.MAX_URGENT_LEVEL

def diffUserInfo(userInfo, userInfoOld, timeStr):
    subjectArr = [ID, "updated"]
    emailMsgArr = []
    isOnlyToolbar = False

    for k in userInfo:
        if userInfo.get(k) != userInfoOld.get(k) and userInfo.get(k) != None:
            subjectArr.append(k)
            if k == 'toolbar_menus':
            # if k in ['toolbar_menus', 'profile_image_url', 'cover_image_phone']:
                emailMsgArr.append(k)
            else:
                emailMsgArr.append([
                    k,
                    userInfoOld.get(k),
                    userInfo.get(k),
                ])
            # 如果 userInfo[profile_image_url] or userInfo['cover_image_phone'] 不同，保存jpg
            if k == 'profile_image_url':
                utils.save_img(userInfo['profile_image_url'], 'log/' + timeStr + '__profile_image_url.jpg')
            if k == 'cover_image_phone':
                utils.save_img(userInfo['cover_image_phone'], 'log/' + timeStr + '__cover_image_phone.jpg')
            if k == 'statuses_count':
                os.system('python get_weibo.py %s' % timeStr)
            if k == 'follow_count':
                print u'拉取关注列表...'
                os.system('python get_following_and_fans.py %s following' % timeStr)
            if k == 'followers_count':
                print u'拉取粉丝列表'
                os.system('python get_following_and_fans.py %s fans' % timeStr)

    if subjectArr == [ID, "updated", 'toolbar_menus']:
        isOnlyToolbar = True
    return emailMsgArr, subjectArr, isOnlyToolbar



def main(urgentLevel):
    # 需要返回的数据
    statusCode = -1
    subject = ''
    emailMsgArr = []
    emailMsgIndent = ''
    emailMsgInline = ''
    isSendEmail = False
    sec, timeStr = utils.init_time(time.localtime())

    print 'sec=%3d timeStr=%s urgentLevel=%d' % (sec, timeStr, urgentLevel)

    utils.append_log('\n' + timeStr + ' ')

    userInfoOld = utils.get_user_info_old()
    userInfo = utils.get_user_info()
    utils.dump_obj_to_file(userInfo, 'temp/temp_uer_info.json')

    if userInfo == {} or userInfoOld == {}:
        statusCode = 1
    if userInfo == userInfoOld:
        statusCode = 0
    else:
        # user_info有变动
        # 1. user_info不完整
        if userInfo.get('id') == None:
            statusCode = 2
            sec = 300
            print "sec=%3d" % sec
        # 2. user_info完整，需要更新log
        else:
            statusCode = 10
            # 保存new_dict
            utils.write_user_info_to_json(userInfo, timeStr)
            emailMsgArr, subjectArr, isOnlyToolbar = diffUserInfo(userInfo, userInfoOld, timeStr)
            subject = " ".join(subjectArr)
            emailMsgIndent = json.dumps(emailMsgArr, indent=4)
            emailMsgInline = json.dumps(emailMsgArr)
            if not isOnlyToolbar:
                isSendEmail = True

            # 提升ul
            urgentLevel = MAX_URGENT_LEVEL
            print "urgentLevel=%d" % (urgentLevel)
    return (statusCode,
            sec,
            urgentLevel,
            subject,
            emailMsgArr,
            emailMsgIndent,
            emailMsgInline,
            isSendEmail,
            timeStr)

os.system('md log')
os.system('md weibo')
os.system('md following')
os.system('md fans')
os.system('md temp')
os.system('md likes')


mainErrCnt = 0
likesErrCnt = 0
urgentLevel = 0
likesObj = likes.Likes()
sec, timeStr = utils.init_time(time.localtime()) # 赋初值，以防万一
statusDict = {
    0: {
        'name': 'not modified',
        'logMsg': 'not modified, '
    },
    1: {
        'name': 'get_user_info failed',
        'logMsg': 'get_user_info failed, '
    },
    2: {
        'name': 'json not completed',
        'logMsg': 'json not completed, '
    },
    10: {
        'name': 'updated',
    }
}
while True:
    try:
        print '============================'
        print 'mainErrCnt=%d likesErrCnt=%d' % (mainErrCnt, likesErrCnt)

        (statusCode,
         sec,
         urgentLevel,
         subject,
         emailMsgArr,
         emailMsgIndent,
         emailMsgInline,
         isSendEmail,
         timeStr) = main(urgentLevel)
        # 0 1 2
        if statusCode in [0, 1, 2]:
            utils.append_log(statusDict[statusCode]['logMsg'])
            title = statusDict[statusCode]['logMsg']
            utils.appendUserInfoToDb(config.ID, timeStr, False, title)
            print statusDict[statusCode]['logMsg']

        # 10
        else:
            utils.append_log(subject + ', ' + emailMsgInline + ', ')
            utils.appendUserInfoToDb(config.ID, timeStr, True, subject, emailMsgInline)
            print subject
            print emailMsgIndent
            if isSendEmail:
                print u'发送邮件...'
                # utils.sendEmail(emailMsgIndent, subject)
                # utils.sendEmail(emailMsgIndent)
                utils.sendHtmlEmailFromDict(emailMsgArr, subject)

        mainErrCnt = 0
    except BaseException, e:

        mainErrCnt += 1
        print u'遇到未知错误'
        logging.exception(e)
        utils.append_log('%s re run main for %s time, ' % (ID, mainErrCnt))
        title = '%s re run main for %s time, ' % (ID, mainErrCnt)
        utils.appendUserInfoToDb(config.ID, timeStr, False, title)
        if mainErrCnt > 10:
            utils.sendEmail('%s terminate main' % ID)
            print u'退出程序'
            break
        else:
            if mainErrCnt > 3:
                utils.sendEmail('%s re run main for %s time' % (ID, mainErrCnt))
            utils.sleep(60)

    # 独立的
    if likesErrCnt <= 5:
        try:
            urgentLevel = likesObj.checkCnt(urgentLevel, timeStr)
            likesErrCnt = 0
        except BaseException, e:
            likesErrCnt += 1
            print u'check_likes_num()错误'
            logging.exception(e)
            if likesErrCnt > 5:
                msg = '%s: likesErrCnt > 5, stopped' % ID
                utils.sendEmail(msg)
                print msg
    # MAX_URGENT_LEVEL - urgentLevel = 0 1 2 3 4 5 6 7 8 9
    # sec = 0 5 20 45 80 125 180 245
    if urgentLevel > 0:
        urgentSec = 0 + 5 * (MAX_URGENT_LEVEL - urgentLevel) ** 2
        if urgentSec < sec:
            sec = urgentSec
            print 'sec=urgentSec, sec=%s' % sec
        else:
            print 'urgentSec=%s, too big, so don\'t change sec' % urgentSec
        urgentLevel -= 1
    utils.sleep(sec)






