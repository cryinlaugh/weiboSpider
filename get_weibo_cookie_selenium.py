#by zwl
#thanks to https://blog.csdn.net/qq_42348937/article/details/85065104

import pickle
from selenium import webdriver

def InitDriver(manually=1):
	chrome_options = webdriver.ChromeOptions()
	#no headless for manually login
	#chrome_options.add_argument('--headless')
	chrome_options.add_argument('--disable-gpu')
	chrome_options.add_argument('window-size=1200,1100')
	driver = webdriver.Chrome(chrome_options=chrome_options,executable_path='./chromedriver-mac')
	return driver

def CloseDriver(driver):
	driver.quit()

def ManuallyLogin(url, driver):
	driver.get(url)
	ret = 0
	while(ret != 'ok' ):
		ret = input("请在网页中登陆微博账号，(登陆后输入ok继续):")
	#print("current url is %s" % driver.current_url)
	cookies = driver.get_cookies()
	saveCookies = {}
	for cookie in cookies:
		saveCookies[cookie['name']] = cookie['value']
	return saveCookies

def SaveCookieToFile(cookies, filename):
	filePath = open(filename, 'wb')
	pickle.dump(cookies, filePath)
	filePath.close()

def SaveCookie():
	driver = InitDriver()
	cookies = ManuallyLogin("https://m.weibo.cn", driver)
	filename = "./WeiboCNCookies"
	SaveCookieToFile(cookies, filename)
	CloseDriver(driver)

	driver = InitDriver()
	cookies = ManuallyLogin("https://weibo.com", driver)
	filename = "./WeiboCOMCookies"
	SaveCookieToFile(cookies, filename)
	CloseDriver(driver)

def main():
	SaveCookie()

if __name__ == '__main__':
	main()
