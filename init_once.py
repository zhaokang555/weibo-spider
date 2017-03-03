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
import logging

URL = config.MAIN_URL
HEADER = config.HEADER



time_str = utils.init_time(time.localtime())[2]
user_info_old = utils.get_user_info_old()
user_info = utils.get_user_info()

if user_info == {} or user_info_old == {}:
    print 'get_user_info failed'
    os._exit(-1)

# 1. user_info不完整
if user_info.get('id') == None:
    print 'json not completed,'
    os._exit(-1)

# 2. user_info完整

os.system('md weibo')
os.system('md following')
os.system('md fans')
os.system('md log')
os.system('md temp')

# 保存new_dict
utils.write_user_info_to_json(user_info, time_str)
print u'拉取关注和粉丝列表...'
os.system('python get_following_and_fans.py %s following' % time_str)
os.system('python get_following_and_fans.py %s fans' % time_str)
print u'拉取最新微博和图片...'
os.system('python get_weibo.py %s' % time_str)

print 'init once finish'
os._exit(0)
