#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# refer to https://github.com/niro8/weibo_crawler

import pandas
import time
import datetime
import re
import random
import logging
import pickle
import json
import os
from selenium import webdriver

chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--disable-gpu')
chrome_options.add_argument('window-size=1200,1100')
driver = webdriver.Chrome(chrome_options=chrome_options,executable_path='./chromedriver-mac')

df = pandas.DataFrame()

need_comments = 'n'

#by zwl
def InitWeiboCNDriverWithCookie():
	chrome_options = webdriver.ChromeOptions()
	chrome_options.add_argument('--headless')
	chrome_options.add_argument('--disable-gpu')
	chrome_options.add_argument('window-size=1200,1100')
	driver_cn = webdriver.Chrome(chrome_options=chrome_options, executable_path='./chromedriver-mac')
	
	driver_cn.get('https://m.weibo.cn')
	
	readPath = open('./WeiboCNCookies','rb')

	cookies = pickle.load(readPath)
	
	for key in cookies:
		driver_cn.add_cookie({
			"domain":".weibo.cn",
			"name":key,
			"value":cookies[key],
			"path":'/',
			"expires":None})
	
	driver_cn.get('https://m.weibo.cn')
	logger.info("Login with cookie, current_url = %s"%driver_cn.current_url)
	readPath.close()
	return driver_cn

#by zwl
def InitWeiboCOMDriverWithCookie():
	driver.get('https://weibo.com')
	readPath = open('./WeiboCOMCookies','rb')
	cookies = pickle.load(readPath)
	for key in cookies:
		driver.add_cookie({
			"domain":".weibo.com",
			"name":key,
			"value":cookies[key],
			"path":'/',
			"expires":None})	
	driver.get('https://weibo.com')
	logger.info("Login with cookie, current_url = %s"%driver.current_url)
	readPath.close()
	return driver


#by zwl
#获取评论
def GetComments(driver, mid):
	df_comments = pandas.DataFrame()

	#请求评论的json(首页)
	url = 'https://m.weibo.cn/comments/hotflow?id=%s&mid=%s&max_id_type=0' % (mid, mid)
	driver.get(url)
	res = "{}"
	try:
		res = driver.find_element_by_xpath('//pre').text
	except Exception:
		logger.error('Something wrong with accessing the first comments page', exc_info=True)
		logger.error(driver.current_url)
		logger.error(driver.page_source)
		return
	resj = json.loads(res)
	n_pages = 0
	#记录首页评论，并请求后续评论页
	#thanks to https://www.jianshu.com/p/8dc04794e35f
	results = []
	while (resj['ok'] == 1 and resj['data']['total_number']>len(results)):
		n_pages = n_pages+1
		#get comments lists
		comms = resj['data']
		#get number of comments in current request
		n_com = len(comms['data'])
		#save comments in current comment page
		for i in range(n_com):
			com = comms['data'][i]
			cominfo = {}
			# com.keys = ['created_at', 'id', 'rootid', 
			# 		  'rootidstr', 'floor_number', 'text', 
			# 		  'disable_reply', 'user', 'mid', 'readtimetype', 
			# 		  'comments', 'max_id', 'total_number', 'isLikedByMblogAuthor', 
			# 		  'more_info_type', 'bid', 'source', 'like_count', 'liked']
			# com['user'].keys = ['id', 'screen_name', 'profile_image_url', 'profile_url', 
			# 				  'statuses_count', 'verified', 'verified_type', 'close_blue_v', 
			# 				  'description', 'gender', 'mbtype', 'urank', 'mbrank', 'follow_me', 
			# 				  'following', 'followers_count', 'follow_count', 'cover_image_phone', 
			# 				  'avatar_hd', 'like', 'like_me', 'badge']
			#choose what you like
			cominfo['评论用户昵称'] = com['user']['screen_name']
			cominfo['发文时间'] = com['created_at']
			cominfo['发文内容'] = com['text']
			cominfo['点赞数'] = com['like_count']
			#logger.info(cominfo)
			results.append(cominfo)
		logger.info("共有评论数：%d，本页页数：%d，本页评论数：%d, 已爬取数：%d" % (comms['total_number'], n_pages, n_com, len(results)))
		#请求后续页
		#获得当前页max_id
		max_id = comms['max_id']
		if(max_id == '0'):
			res = '{\"ok\":0}'
			continue
		#logger.info("Max_id of current page %s"%max_id)
		url = 'https://m.weibo.cn/comments/hotflow?id=%s&mid=%s&max_id=%s&max_id_type=0' % (mid, mid, max_id)
		time.sleep(random.randint(5,10))
		driver.get(url)
		try:
			res = driver.find_element_by_xpath('//pre').text
		except Exception:
			logger.error('Something wrong with accessing the first comments page', exc_info=True)
			logger.error(driver.current_url)
			logger.error(driver.page_source)
			res = '{\"ok\":0}'
		resj = json.loads(res)
	#logger.info(resj)
	
	df_comments = df_comments.append(results)
	filePath = './output/comments/comm_%s.xlsx' % mid
	df_comments.to_excel(filePath,index=0)
	logger.info('已导出微博%s的评论条数：%s' % (mid,len(results)))
	return 

#by zwl
def GetAndSaveComments(mid):
	logger.info(">>>>开始抓取微博(%s)的评论>>>>" % mid)
	driver = InitWeiboCNDriverWithCookie()
	GetComments(driver,mid)
	driver.quit()

# 搜索
def GetSearchContent():
	ok = 0
	key=''
	start_time = ''
	end_time = ''
	global need_comments
	while(ok !='ok'):
		key = input("请输入搜索关键词：")
		start_time = input("请输入搜索起始日期和时间（yyyy-mm-dd-h):")
		end_time = input("请输入搜索结束日期和时间（yyyy-mm-dd-h):")
		need_comments = input("是否同时抓取一级评论（y/n):")
		ok = input("确认以上输入无误后，输入ok继续，否则直接继续可重新输入:")
	driver.get("http://s.weibo.com/")
	logger.info('搜索热点主题：%s' % key)
	driver.find_element_by_xpath("//input").send_keys(key)
	time.sleep(3)
	driver.find_element_by_xpath('//button').click()
	current_url = driver.current_url.split('&')[0]
	url = current_url+'&xsort=hot&suball=1&timescope=custom:'+ start_time + ':' + end_time + '&Refer=g'
	driver.get(url)
	handlePage()
	filePath = './output/%s-%s-%s.xlsx' % (key, start_time, end_time)
	df.to_excel(filePath,index=0)
	logger.info('已导出微博条数：%s' % len(df))

# 处理页面，检查是否有内容，有内容进行爬取
def handlePage():
	page = 1
	while True:
		time.sleep(random.randint(5,10))
		if checkContent():
			logger.info('页数:%s' % page)
			getContent()
			page += 1
			if checkNext():
				driver.find_element_by_xpath('//div[@class="m-page"]/div/a[@class="next"]').click()
			else:
				logger.info("no Next")
				break
		else:
			logger.info("no Content")
			break

# 检查页面是否有内容
def checkContent():
	try:
		driver.find_element_by_xpath("//div[@class='card card-no-result s-pt20b40']")
		flag = False
	except:
		flag = True
	return flag

# 检查是否有下一页
def checkNext():
	try:
		driver.find_element_by_xpath('//div[@class="m-page"]/div/a[@class="next"]')
		flag = True
	except:
		flag = False
	return flag

# 处理时间
def get_datetime(s):
	try:
		today = datetime.datetime.today()
		if '今天' in s:
			H, M = re.findall(r'\d+',s)
			date = datetime.datetime(today.year, today.month, today.day, int(H), int(M)).strftime('%Y-%m-%d %H:%M')
		elif '年' in s:
			y, m, d, H, M = re.findall(r'\d+',s)
			date = datetime.datetime(int(y), int(m), int(d), int(H), int(M)).strftime('%Y-%m-%d %H:%M')                       
		else:    
			m, d, H, M = re.findall(r'\d+',s)
			date = datetime.datetime(today.year, int(m), int(d), int(H), int(M)).strftime('%Y-%m-%d %H:%M')
	except:
		date = s
	return date


# 获取内容
def getContent():
	nodes = driver.find_elements_by_xpath('//div[@class="card-wrap"][@action-type="feed_list_item"][@mid]')
	if len(nodes) == 0:
		time.sleep(random.randint(20,30))
		driver.get(driver.current_url)
		getContent()
	results = []
	global df
	logger.info('微博数量：%s' % len(nodes))
	for i in range(len(nodes)):
		blog = {}
		try:
			BZNC = nodes[i].find_element_by_xpath('.//a[@class="name"]').get_attribute('nick-name')
		except:
			BZNC = ''
		blog['博主昵称'] = BZNC
		
		try:
			BZZY = nodes[i].find_element_by_xpath('.//a[@class="name"]').get_attribute("href")
		except:
			BZZY = ''
		blog['博主主页'] = BZZY
		
		try:
			#是否需要展开全文
			nodes[i].find_element_by_xpath('.//p[@class="txt"][@node-type="feed_list_content"]/a[@action-type="fl_unfold"]').click()
			WBNR = nodes[i].find_element_by_xpath('.//p[@class="txt"][@node-type="feed_list_content_full"]').text
			#logger.info('Find Second! %d' % i)
			#logger.info('%s' % WBNR) 
			#如果为转发微博（搜热点基本上没有）
			if len(nodes[i].find_elements_by_xpath('.//p[@class="txt"][@node-type="feed_list_content_full"]'))>1:
				WBNR = WBNR + '\n转发：' +nodes[i].find_element_by_xpath('.//div[@node-type="feed_list_forwardContent"]').text
			 #去掉“收起全文”几个字
			if(WBNR[len(WBNR)-5:]== '收起全文d'):
				WBNR = WBNR[:len(WBNR)-5]
		except:
			try: 
				WBNR = nodes[i].find_element_by_xpath('.//p[@class="txt"][@node-type="feed_list_content"]').text
				#logger.info('Find First! %d' % i)
				#logger.info('%s' % WBNR)
				if len(nodes[i].find_elements_by_xpath('.//p[@class="txt"][@node-type="feed_list_content"]'))>1:
					WBNR = WBNR + '\n转发：' +nodes[i].find_element_by_xpath('.//div[@node-type="feed_list_forwardContent"]').text
			except:
				WBNR = ''
		blog['微博内容'] = WBNR
		try:
			FBSJ = nodes[i].find_element_by_xpath('.//div[@class="content"]/p[@class="from"]/a[1]').text
		except:
			FBSJ = ''
		blog['发布时间'] = get_datetime(FBSJ)
		try:
			WBDZ = nodes[i].find_element_by_xpath('.//div[@class="content"]/p[@class="from"]/a[1]').get_attribute("href")
		except:
			WBDZ = ''
		blog['微博地址'] = WBDZ
		try:
			WBLY = nodes[i].find_element_by_xpath('.//div[@class="content"]/p[@class="from"]/a[2]').text
		except:
			WBLY = ''
		blog['微博来源'] = WBLY
		try:
			ZF_TEXT = nodes[i].find_element_by_xpath('.//div[@class="card-act"]/ul/li[2]').text.replace('转发','').strip()
			if ZF_TEXT == '':
				ZF = 0
			else:
				ZF = int(ZF_TEXT)
		except:
			ZF = 0
		blog['转发'] = ZF
		
		try:
			PL_TEXT = nodes[i].find_element_by_xpath('.//div[@class="card-act"]/ul/li[3]').text.replace('评论','').strip()
			if PL_TEXT == '':
				PL = 0
			else:
				PL = int(PL_TEXT)
		except:
			PL = 0
		blog['评论'] = PL

		try:
			ZAN_TEXT = nodes[i].find_element_by_xpath('.//div[@class="card-act"]/ul/li[4]/a/em').text
			if ZAN_TEXT == '':
				ZAN = 0
			else:
				ZAN = int(ZAN_TEXT)
		except:
			ZAN = 0
		blog['赞'] = ZAN

		try:
			mid = nodes[i].get_attribute('mid')
			#logger.info(mid)
			#mid = int(mid)	
		except Exception:
			mid = -1
		blog['mid'] = mid

		#by zwl 爬取评论
		#logger.info("抓去评论？%s" % need_comments)

		results.append(blog)
	df = df.append(results)
	

def main():
	#for geting weibos 
	InitWeiboCOMDriverWithCookie()
	GetSearchContent()
	
	##for getting comments

	#global df
	#df = pandas.DataFrame(pandas.read_excel("./output/瑞典辱华-2018-09-22-0-2018-09-23-0.xlsx"))
	for mid in df['mid']:
		if(os.path.exists("./output/comments/comm_%s.xlsx"%mid)):
			logger.info("comments of %s already exists."%mid)
		else:
			GetAndSaveComments(mid)
	time.sleep(3)
	driver.quit()


if __name__ == '__main__':
	logger = logging.getLogger(__name__)
	logger.setLevel(logging.INFO)
	handler = logging.FileHandler('export_record.log')
	handler.setLevel(logging.INFO)
	console = logging.StreamHandler()
	console.setLevel(logging.INFO)
	formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
	handler.setFormatter(formatter)
	console.setFormatter(formatter)
	logger.addHandler(handler)
	logger.addHandler(console)
	logger.info('*'*30+'START'+'*'*30)
	main()
	logger.info('*'*30+'E N D'+'*'*30)
