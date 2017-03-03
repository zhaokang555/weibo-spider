#!/usr/bin/env python
# -*- coding: utf-8 -*-

import urllib2
import config
import random
import codecs
import json
import re
import os
import utils
import requests
import config2
import time
import logging

MAX_URGENT_LEVEL = config2.MAX_URGENT_LEVEL

# ==============
# likes
# ==============

class Likes:
    # ====================================================================
    # 调试函数
    def testUrl(self, url):
        r = self.session.get(url,
                             timeout=self.timeoutTuple,
                             headers=self.headers
                             )
        print r.text

    def printCookieDict(self):
        print requests.utils.dict_from_cookiejar(self.session.cookies)
    # ====================================================================


    def _getLikesNum(self):
        likesNum = -1
        if self.getLikesNumErrCnt <= 3:
            r = requests.get(self.likesUrl, timeout=self.timeoutTuple, headers=self.headers)
            likesNumStr = r.json().get('cards')[0].get('card_group')[0].get('desc1')
            search_result = re.search(u'(\\d{0,})条赞过的微博', likesNumStr)
            if search_result:
                self.getLikesNumErrCnt = 0
                likesNum = int(search_result.group(1))
            else:
                self.getLikesNumErrCnt += 1
                utils.sleep(5)
                self._getLikesNum()
        return likesNum

    def _getLikesNumOld(self):
        likesNumOld = -1
        try:
            f_in = codecs.open('temp/likes_num_old.json', 'r')
            likesNumOld = json.load(f_in)
        except IOError, e:
            # 没有likes_num_old.json
            likesNumOld = self._getLikesNum()
            with codecs.open('temp/likes_num_old.json', 'w', 'utf-8') as f_in:
                json.dump(likesNumOld, f_in, ensure_ascii=False, indent=4)
        finally:
            if f_in:
                f_in.close()
            return likesNumOld

    # 保存详情json
    def _saveWeibo(self):
        r = requests.get(config.LIKES_WEIBO_URL, timeout=config.TIMEOUT_TUPLE, headers=config.HEADER_WITH_COOKIE)
        folderName = '%s__%d_to_%d' % (self.timeStr, self.likesNumOld, self.likesNum)
        os.system('md likes\\%s' % folderName)
        self.filePath = 'likes/%s/raw.json' % folderName
        print 'saving %s' % self.filePath
        utils.dump_obj_to_file(r.json(), self.filePath)
        self._filtWeiboAndSave()
        return self.filePath


    def _filtWeiboAndSave(self):
        # for test
        folderPath = os.path.split(self.filePath)[0]
        self.filtedFilePath = folderPath + '/' + 'filted.json'

        with codecs.open(self.filePath, 'r', encoding='utf-8') as f:
            d = json.load(f)

        # ok == 1
        if d.get('ok') and d.get('cards'):
            cards = d.get('cards')
            utils.filtCards(cards)
            print 'saving %s' % self.filtedFilePath
            utils.dump_obj_to_file(cards, self.filtedFilePath)


    def __init__(self):
        self.timeStr = '000'
        self.session =  requests.session()
        self.likesUrl = config.LIKES_URL
        self.timeoutTuple = config.TIMEOUT_TUPLE
        self.headers = config.HEADER
        self.getLikesNumErrCnt = 0

    def checkCnt(self, urgentLevel, timeStr):
        self.timeStr = timeStr
        self.likesNumOld = self._getLikesNumOld()
        self.likesNum = self._getLikesNum()
        print 'likesNumOld=%d likesNum=%d' % (self.likesNumOld, self.likesNum)
        if self.likesNumOld != self.likesNum:
            # 保存详情json
            self._saveWeibo()

            # 更新 likes_num_old
            utils.dump_obj_to_file(self.likesNum, 'temp/likes_num_old.json')

            # 邮件，日志
            emailMsg = '%s updated: likesNum from %s to %s, ' % (config.ID, self.likesNumOld, self.likesNum)
            print emailMsg
            utils.append_log(emailMsg)
            utils.appendLikesToDb(config.ID, self.timeStr, True, self.likesNumOld, self.likesNum)
            # utils.sendEmail(emailMsg)
            utils.sendEmailWithFileLst(emailMsg, [self.filePath, self.filtedFilePath], config.ID + ' likes 和 附件')

            # 提升UL
            urgentLevel = MAX_URGENT_LEVEL
            print 'urgentLevel=%s' % urgentLevel
        else:
            print 'likesNum not modified'
            utils.appendLikesToDb(config.ID, self.timeStr, False, self.likesNumOld, self.likesNum)

        return urgentLevel

