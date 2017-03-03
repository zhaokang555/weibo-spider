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
import logging

HEADER = config.HEADER_WITH_COOKIE
TIMEOUT_TUPLE = config.TIMEOUT_TUPLE
TIME_STR = sys.argv[1]
FOLDER = sys.argv[2]

URL = ''
if FOLDER == 'following':
    URL = config.GET_FOLLOWING_URL
if FOLDER == 'fans':
    URL = config.GET_FANS_URL

errCnt = 0
def get_total_page_num():
    global errCnt
    r = requests.get(URL + str(errCnt+1), headers=config.HEADER_WITH_COOKIE, timeout=config.TIMEOUT_TUPLE)
    txt = r.text
    utils.write_txt_to_file(txt, 'temp/temp.html')
    searchObj = re.search(u'<input type="submit" value="跳页" />&nbsp;(\\d+)/(\\d+)页', txt)
    searchObj2 = re.search(u'关注以上这些人', txt)
    totalPageNum = 0
    print 'searchObj: ', searchObj
    print 'searchObj2: ', searchObj2
    if searchObj != None:
        totalPageNum = int(searchObj.group(2))
        errCnt = 0
    elif searchObj2 != None:
        totalPageNum = 1
    else:
        errCnt += 1
        if errCnt <= 3:
            print 're try to get totalPageNum, sleep 500 s ...'
            time.sleep(500)
            totalPageNum = get_total_page_num(URL)
        else:
            sys.exit()
    if totalPageNum > 888:
        totalPageNum = 888
    return totalPageNum

def get_and_save_html():
    totalPageNum = 0
    totalPageNum = get_total_page_num()
    if totalPageNum == 0:
        print 'totalPageNum = 0, exit'
        sys.exit()

    for pageNum in range(1, totalPageNum + 1):
        txt = requests.get(URL + str(pageNum), headers=HEADER, timeout=TIMEOUT_TUPLE).text
        htmlPath = '%s/%s/%s__%03d.html' % (FOLDER, TIME_STR, FOLDER, pageNum)
        # print 'saving %s' % htmlPath
        utils.write_txt_to_file(txt, htmlPath)

    return totalPageNum


def main():
    os.system('md %s\\%s' % (FOLDER, TIME_STR))
    totalPageNum = get_and_save_html()
    os.system('node get_following_and_fans.js "%s" "%s" "%d"' % (FOLDER, TIME_STR, totalPageNum))
    filtedFilePath = FOLDER + '/' + TIME_STR + '/' + FOLDER + '__filted.json'
    utils.sendEmailWithFileLst(FOLDER + ' ' + TIME_STR, [filtedFilePath])

main()
