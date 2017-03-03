#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import config
import requests
import codecs
import utils
import re
import time
import urllib2
import random
import json
import likes
import sqlite3
import logging


class AllLikes:
    def _updateTimeStr(self):
        lt = time.localtime()
        self.timeStr = '%d_%02d_%02d__%02d_%02d_%02d' % (lt[0], lt[1], lt[2], lt[3], lt[4], lt[5])

    def _processRDict(self, rDict):
        # 保存原始json
        rawFilePath = 'all_likes/%s/raw/page_%05d.json' % (self.timeStr, self.pageCnt)
        print 'saving %s' % rawFilePath
        utils.dump_obj_to_file(rDict, rawFilePath)

        # 过滤
        cards = rDict.get('cards')
        self.totalWeiboNum += len(cards)
        utils.filtCards(cards)

        # 保存过滤后的json
        filtedFilePath = 'all_likes/%s/filted/page_%05d.json' % (self.timeStr, self.pageCnt)
        print 'saving %s' % filtedFilePath
        utils.dump_obj_to_file(cards, filtedFilePath)

        # 重命名
        utils.renameFiltedCards(cards)

        # 保存重命名后的json
        renamedFilePath = 'all_likes/%s/renamed/page_%05d.json' % (self.timeStr, self.pageCnt)
        print 'saving %s' % renamedFilePath
        utils.dump_obj_to_file(cards, renamedFilePath)

    def run(self):
        self._updateTimeStr()
        os.system('md all_likes\\%s' % self.timeStr)
        os.system('md all_likes\\%s\\raw' % self.timeStr)
        os.system('md all_likes\\%s\\filted' % self.timeStr)
        os.system('md all_likes\\%s\\renamed' % self.timeStr)
        while(self.pageCnt <= 999):
            r = requests.get(self.url + '&page=%d' % self.pageCnt, timeout=config.TIMEOUT_TUPLE, headers=config.HEADER_WITH_COOKIE)
            rDict = r.json()
            if rDict.get('cards'):
                self.getPageErrCnt = 0
                self._processRDict(rDict)
                if self.pageCnt % 10 == 0:
                    utils.sleep(300)
                self.pageCnt += 1
            # 结束
            elif rDict.get('ok') and not rDict.get('cards'):
                # 保存结束的json以备后用
                rawFilePath = 'all_likes/%s/raw/page_%05d.json' % (self.timeStr, self.pageCnt)
                print 'saving %s' % rawFilePath
                utils.dump_obj_to_file(rDict, rawFilePath)

                self.totalPageNum = self.pageCnt - 1
                print self.totalPageNum
                break
            # 拉取失败
            elif not rDict.get('cards'):
                self.getPageErrCnt += 1
                if self.getPageErrCnt < self.maxErrCnt:
                    print 'retry to get page %s' % self.pageCnt
                    utils.sleep(5)
                else:
                    print 'failed to get page %s, exit' % self.pageCnt
                    break

    def __init__(self, url=config.LIKES_WEIBO_URL):
        os.system('md all_likes')
        # init all props

        self.url = url
        self.pageCnt = 1
        self.totalPageNum = self.pageCnt
        self.timeStr = '000'
        self.getPageErrCnt = 0
        self.maxErrCnt = 5
        self.totalWeiboNum = 0


if __name__ == '__main__':
    AllLikes().run()

