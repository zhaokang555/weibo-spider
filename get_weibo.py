#!/usr/bin/env python
# -*- coding: utf-8 -*-

# run cmd: python get_weibo.py "time_str"


import urllib2
import json
import codecs
import os
import sys
import utils
import config
import requests
import time
import logging

IMG_CNT = 0
PAGE_NUM = 1
TOTAL_PAGE_NUM = PAGE_NUM
URL = config.GET_WEIBO_URL
HEADER = config.HEADER_WITH_COOKIE
TIMEOUT = config.TIMEOUT
TIMEOUT_TUPLE = config.TIMEOUT_TUPLE


def get_weibo_dict(url):
    # request = urllib2.Request(url, headers=HEADER)
    # response = urllib2.urlopen(request, timeout=TIMEOUT)
    # res_txt = response.read()
    # print res_txt
    # response_dict = json.loads(res_txt)
    # return response_dict

    # ===============
    # 新方法
    r = requests.get(url, timeout=TIMEOUT_TUPLE, headers=HEADER)
    return r.json()

def filt_and_write_two_dict_to_file(raw_dict, time_str):
    def filt_pics_arr_and_save_img(arr, time_str, tag):


        global IMG_CNT

        for item in arr:
            for (k, v) in item.items():
                if k == 'large':
                    large = item['large']
                    for (k, v) in large.items():
                        if k in ['url']:
                            url = large['url']
                            ext_name = url.split('.')[-1]
                            path = 'weibo/%s/page%03d/%03d__%s.%s' % (time_str, PAGE_NUM, IMG_CNT, tag, ext_name)
                            print 'saving ', path
                            utils.save_img(url, path)
                            IMG_CNT = IMG_CNT + 1
                        else:
                            large.pop(k)
                else:
                    item.pop(k)

    global PAGE_NUM

    # 1
    path = 'weibo/%s/page%03d/raw.json' % (time_str, PAGE_NUM)
    print 'saving ', path
    f_raw = codecs.open(path, 'w', 'utf-8')
    json.dump(raw_dict, f_raw, ensure_ascii=False, indent=4)
    f_raw.close()


    # 2.1 清理
    for (k, v) in raw_dict.items():
        if k in ['cards', 'cardlistInfo']:
            for (k, v) in raw_dict['cardlistInfo'].items():
                if k in ['total']:
                    pass
                else:
                    raw_dict['cardlistInfo'].pop(k)
            for card in raw_dict['cards']:
                if card.get('mblog') == None:
                    raw_dict['cards'].remove(card)
                for (k, v) in card.items():
                    if k in ['mblog']:
                        for (k, v) in card['mblog'].items():
                            if k in ['comments_count', 'created_at', 'retweeted_status', 'text', 'pics', 'attitudes_count', 'reposts_count']:
                                if k in ['retweeted_status']:
                                    retweeted_status = card['mblog']['retweeted_status']
                                    for (k, v) in retweeted_status.items():
                                        if k in ['attitudes_count', 'comments_count', 'created_at', 'pics', 'reposts_count', 'text']:
                                            # ======2.2
                                            pass
                                        else:
                                            retweeted_status.pop(k)
                                # ======2.2
                            else:
                                card['mblog'].pop(k)
                    else:
                        card.pop(k)
        else:
            raw_dict.pop(k)

    # 2.2 清理cards
    cards = raw_dict['cards']
    for card in cards:
        pics = []
        re_pics = []
        if card['mblog'].get('pics') != None:
            pics = card['mblog'].get('pics')
        if card['mblog'].get('retweeted_status') != None:
            retweeted_status = card['mblog'].get('retweeted_status')
            if retweeted_status.get('pics') != None:
                re_pics = retweeted_status.get('pics')

        filt_pics_arr_and_save_img(pics, time_str, 'original')
        filt_pics_arr_and_save_img(re_pics, time_str, 'forward')

    # 3.
    path = 'weibo/%s/page%03d/filted.json' % (time_str, PAGE_NUM)
    print 'saving ', path
    f_filted = codecs.open(path, 'w', 'utf-8')
    json.dump(raw_dict, f_filted, ensure_ascii=False, indent=4)
    f_filted.close()

def main():
    global PAGE_NUM
    global TOTAL_PAGE_NUM
    time_str = sys.argv[1]
    
    os.system('md weibo\\%s' % time_str)
    
    while True:
        print 'PAGE_NUM', PAGE_NUM
        raw_dict = get_weibo_dict(URL + str(PAGE_NUM))
        if (raw_dict.get('ok') != 1 or len(raw_dict.get('cards')) == 0):
            print 'retry get next page weibo'
            utils.sleep(5)
            raw_dict = get_weibo_dict(URL + str(PAGE_NUM))
            if (raw_dict.get('ok') != 1 or len(raw_dict.get('cards')) == 0):
                print 'total page: %s' % (PAGE_NUM - 1)
                TOTAL_PAGE_NUM = PAGE_NUM - 1
                break

        os.system('md weibo\\%s\\page%03d' % (time_str, PAGE_NUM))
        filt_and_write_two_dict_to_file(raw_dict, time_str)
        PAGE_NUM += 1
    print 'get_weibo done'

    # 发送附件
    fileLst = []
    for i in range(1, TOTAL_PAGE_NUM):
        file = 'weibo/%s/page%03d/filted.json' % (time_str, i)
        fileLst.append(file)
    utils.sendEmailWithFileLst('%s %s pages weibo' % (time_str, TOTAL_PAGE_NUM), fileLst)

main()