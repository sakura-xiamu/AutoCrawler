"""
Copyright 2018 YoongiKim

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
"""

import time
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.common.exceptions import ElementNotVisibleException, StaleElementReferenceException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import json
from urllib.parse import urlparse, parse_qs, unquote, urlunparse
from LinkFilter import LinkFilter


class CollectLinks:
    def __init__(self, no_gui=False, proxy=None):
        chrome_options = Options()
        chrome_options.add_argument('--no-sandbox')  # To maintain user cookies
        chrome_options.add_argument('--disable-dev-shm-usage')
        if no_gui:
            chrome_options.add_argument('--headless')
        if proxy:
            chrome_options.add_argument("--proxy-server={}".format(proxy))
        self.browser = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        self.filter = LinkFilter()
        
        browser_version = 'Failed to detect version'
        chromedriver_version = 'Failed to detect version'
        major_version_different = False

        if 'browserVersion' in self.browser.capabilities:
            browser_version = str(self.browser.capabilities['browserVersion'])

        if 'chrome' in self.browser.capabilities:
            if 'chromedriverVersion' in self.browser.capabilities['chrome']:
                chromedriver_version = str(self.browser.capabilities['chrome']['chromedriverVersion']).split(' ')[0]

        if browser_version.split('.')[0] != chromedriver_version.split('.')[0]:
            major_version_different = True

        print('_________________________________')
        print('Current web-browser version:\t{}'.format(browser_version))
        print('Current chrome-driver version:\t{}'.format(chromedriver_version))
        if major_version_different:
            print('warning: Version different')
            print(
                'Download correct version at "http://chromedriver.chromium.org/downloads" and place in "./chromedriver"')
        print('_________________________________')

    def get_scroll(self):
        pos = self.browser.execute_script("return window.pageYOffset;")
        return pos

    def wait_and_click(self, xpath):
        #  Sometimes click fails unreasonably. So tries to click at all cost.
        try:
            w = WebDriverWait(self.browser, 15)
            elem = w.until(EC.element_to_be_clickable((By.XPATH, xpath)))
            elem.click()
            self.highlight(elem)
        except Exception as e:
            print('Click time out - {}'.format(xpath))
            print('Refreshing browser...')
            self.browser.refresh()
            time.sleep(2)
            return self.wait_and_click(xpath)

        return elem

    def highlight(self, element):
        self.browser.execute_script("arguments[0].setAttribute('style', arguments[1]);", element,
                                    "background: yellow; border: 2px solid red;")

    @staticmethod
    def remove_duplicates(_list):
        return list(dict.fromkeys(_list))

    def google(self, keyword, add_url=""):
        #self.browser.get("https://www.google.com/search?q={}&source=lnms&tbm=isch{}".format(keyword, add_url))
        self.browser.get("https://www.google.com/search?q={}&source=lnms&udm=2&tbs=isz:l".format(keyword, add_url))

        time.sleep(1)

        print('Scrolling down')

        elem = self.browser.find_element(By.TAG_NAME, "body")

        last_scroll = 0
        scroll_patience = 0
        NUM_MAX_SCROLL_PATIENCE = 50

        while True:
            elem.send_keys(Keys.PAGE_DOWN)
            time.sleep(0.2)

            scroll = self.get_scroll()
            if scroll == last_scroll:
                scroll_patience += 1
            else:
                scroll_patience = 0
                last_scroll = scroll

            if scroll_patience >= NUM_MAX_SCROLL_PATIENCE:
                break

        print('Scraping links')

        imgs = self.browser.find_elements(By.XPATH, '//*[@class="YQ4gaf"]')

        links = []
        for idx, img in enumerate(imgs):
            try:
                src = img.get_attribute("src")
                links.append(src)

            except Exception as e:
                print('[Exception occurred while collecting links from google] {}'.format(e))

        links = self.remove_duplicates(links)

        print('Collect links done. Site: {}, Keyword: {}, Total: {}'.format('google', keyword, len(links)))
        self.browser.close()

        filter = LinkFilter()
        filtered_links = filter.filter_links(links)
        return filtered_links

    def naver(self, keyword, add_url=""):
        self.browser.get(
            "https://search.naver.com/search.naver?where=image&sm=tab_jum&query={}{}".format(keyword, add_url))

        time.sleep(1)

        print('Scrolling down')

        elem = self.browser.find_element(By.TAG_NAME, "body")

        for i in range(60):
            elem.send_keys(Keys.PAGE_DOWN)
            time.sleep(0.2)
            if self.is_scroll_end:
                # 如果触底了就暂停5秒
                print('naver触底暂停')
                time.sleep(5)

        imgs = self.browser.find_elements(By.XPATH, '//div[@class="tile_item _fe_image_tab_content_tile"]//img[@class="_fe_image_tab_content_thumbnail_image"]')

        print('Scraping links')

        links = []

        for img in imgs:
            try:
                src = img.get_attribute("src")
                if src[0] != 'd':
                    new_url = unquote(src)
                    query = urlparse(new_url).query
                    # 解析查询参数
                    params = parse_qs(query)
                    # 解析 URL
                    parsed_url = urlparse(params['src'][0])
                    # 去掉查询参数和片段
                    new_url = urlunparse((parsed_url.scheme, parsed_url.netloc, parsed_url.path, '', '', ''))
                    is_subdomain = self.is_subdomain(new_url, 'pexels.com')
                    if is_subdomain:
                        new_url += '?auto=compress&cs=tinysrgb&dpr=1&w=640&h=640'
                    links.append(new_url)
            except Exception as e:
                print('[Exception occurred while collecting links from naver] {}'.format(e))

        links = self.remove_duplicates(links)

        print('Collect links done. Site: {}, Keyword: {}, Total: {}'.format('naver', keyword, len(links)))
        self.browser.close()

        filter = LinkFilter()
        filtered_links = filter.filter_links(links)
        return filtered_links

    def bing(self, keyword, add_url=""):
        self.browser.get(
            "https://www.bing.com/images/search?first=1&q={}{}".format(keyword, add_url))

        time.sleep(1)

        print('Scrolling down')

        elem = self.browser.find_element(By.TAG_NAME, "body")

        for i in range(20):
            elem.send_keys(Keys.PAGE_DOWN)
            time.sleep(0.2)
            #if i % 2 == 0 :
                #elem.send_keys(Keys.PAGE_UP)

            # 执行 JavaScript 获取页面滚动信息
            scroll_info = self.browser.execute_script(
                "return {"
                "    scrollTop: document.documentElement.scrollTop || document.body.scrollTop,"
                "    clientHeight: document.documentElement.clientHeight || window.innerHeight,"
                "    scrollHeight: document.documentElement.scrollHeight || document.body.scrollHeight"
                "};"
            )
            # 判断是否到底部
            is_scroll_end = scroll_info['scrollTop'] + scroll_info['clientHeight'] >= scroll_info['scrollHeight']
            # 判断是否到底部
            if is_scroll_end :
                print("已经滚动到底部")
                elem.send_keys(Keys.PAGE_UP)
                # 执行 JavaScript 获取页面滚动信息
                scroll_info = self.browser.execute_script(
                    "return {"
                    "    scrollTop: document.documentElement.scrollTop || document.body.scrollTop,"
                    "    clientHeight: document.documentElement.clientHeight || window.innerHeight,"
                    "    scrollHeight: document.documentElement.scrollHeight || document.body.scrollHeight"
                    "};"
                )
                # 判断是否到底部
                is_scroll_end = scroll_info['scrollTop'] + scroll_info['clientHeight'] >= scroll_info['scrollHeight']
                if is_scroll_end :
                    time.sleep(2)
                    elem.send_keys(Keys.PAGE_UP)
                    #self.wait_and_click('//button[@class="Button_button__RDDf5 spacing_noMargin__F5u9R spacing_pr30__J0kZ7 spacing_pl30__01iHm Grid_loadMore__hTWju Button_clickable__DqoNe Button_color-white__Wmgol"]')

        imgs = self.browser.find_elements(By.XPATH, '//a[@class="iusc"]')

        print('Scraping links')

        links = []

        for img in imgs:
            try:
                attr_m = img.get_attribute("m")
                if attr_m:
                    json_m = json.loads(attr_m)
                    links.append(json_m['murl'])
            except Exception as e:
                print('[Exception occurred while collecting links from bing] {}'.format(e))

        links = self.remove_duplicates(links)

        print('Collect links done. Site: {}, Keyword: {}, Total: {}'.format('bing', keyword, len(links)))
        self.browser.close()

        filtered_links = self.filter.filter_links(links)
        return filtered_links

    def pexels(self, keyword, add_url=""):
        self.browser.get(
            "https://www.pexels.com/search/{}{}".format(keyword, add_url))

        time.sleep(1)

        print('Scrolling down')

        elem = self.browser.find_element(By.TAG_NAME, "body")

        count = 0
        for i in range(200):
            elem.send_keys(Keys.PAGE_DOWN)
            time.sleep(1)
            #if i % 3 == 0 :
                #elem.send_keys(Keys.PAGE_UP)

            # 判断是否到底部
            is_scroll_end = self.is_scroll_end()
            # 判断是否到底部
            if is_scroll_end :
                print("pexels 已经滚动到底部 {}".format(i))
                for j in range(5):
                    elem.send_keys(Keys.PAGE_UP)

                # 判断是否到底部
                is_scroll_end = self.is_scroll_end()
                if is_scroll_end:
                    print("pexels 二次滚动到底部 {}".format(i))
                    for j in range(5):
                        elem.send_keys(Keys.PAGE_UP)
                        time.sleep(1)

                    count += 0
                    if count > 5:
                        break
                else:
                    count = 0
                    #self.wait_and_click('//button[@class="Button_button__RDDf5 spacing_noMargin__F5u9R spacing_pr30__J0kZ7 spacing_pl30__01iHm Grid_loadMore__hTWju Button_clickable__DqoNe Button_color-white__Wmgol"]')

        imgs = self.browser.find_elements(By.XPATH, '//a//img[@class="spacing_noMargin__F5u9R"]')

        print('Scraping links')

        links = []

        for img in imgs:
            try:
                src = img.get_attribute("src")
                if src:
                    # 替换 w=500 为 w=640
                    new_url = src.replace("w=500", "w=640&h=640")
                    links.append(new_url)
            except Exception as e:
                print('[Exception occurred while collecting links from pexels] {}'.format(e))

        links = self.remove_duplicates(links)

        print('Collect links done. Site: {}, Keyword: {}, Total: {}'.format('pexels', keyword, len(links)))
        self.browser.close()

        filtered_links = self.filter.filter_links(links)
        return filtered_links

    def google_full(self, keyword, add_url="", limit=100):
        print('[Full Resolution Mode]')

        self.browser.get("https://www.google.com/search?q={}&tbm=isch{}".format(keyword, add_url))
        time.sleep(1)

        # Click the first image to get full resolution images
        self.wait_and_click('//*[@class="YQ4gaf"]')
        time.sleep(1)

        body = self.browser.find_element(By.TAG_NAME, "body")

        print('Scraping links')

        links = []
        limit = 10000 if limit == 0 else limit
        count = 1
        last_scroll = 0
        scroll_patience = 0
        NUM_MAX_SCROLL_PATIENCE = 100

        while len(links) < limit:
            try:
                # Google renders compressed image first, and overlaps with full image later.
                xpath = '//div[@jsname="figiqf"]//img[not(contains(@src,"gstatic.com"))]'

                t1 = time.time()
                while True:
                    imgs = body.find_elements(By.XPATH, xpath)
                    t2 = time.time()
                    if len(imgs) > 0:
                        break
                    if t2 - t1 > 5:
                        print(f"Failed to locate image by XPATH: {xpath}")
                        break
                    time.sleep(0.1)

                if len(imgs) > 0:
                    self.highlight(imgs[0])
                    src = imgs[0].get_attribute('src')

                    if src is not None and src not in links:
                        links.append(src)
                        print('%d: %s' % (count, src))
                        count += 1
            except KeyboardInterrupt:
                break
                
            except StaleElementReferenceException:
                # print('[Expected Exception - StaleElementReferenceException]')
                pass
            except Exception as e:
                print('[Exception occurred while collecting links from google_full] {}'.format(e))

            scroll = self.get_scroll()
            if scroll == last_scroll:
                scroll_patience += 1
            else:
                scroll_patience = 0
                last_scroll = scroll

            if scroll_patience >= NUM_MAX_SCROLL_PATIENCE:
                break

            body.send_keys(Keys.RIGHT)

        links = self.remove_duplicates(links)

        print('Collect links done. Site: {}, Keyword: {}, Total: {}'.format('google_full', keyword, len(links)))
        self.browser.close()

        filter = LinkFilter()
        filtered_links = filter.filter_links(links)
        return filtered_links

    def naver_full(self, keyword, add_url=""):
        print('[Full Resolution Mode]')

        return self.naver(keyword, add_url)

    def bing_full(self, keyword, add_url="", limit=100):
        print('[Full Resolution Mode]')

        self.browser.get(
            "https://www.bing.com/images/search?first=1&q={}{}".format(keyword, add_url))
        time.sleep(1)

        # Click the first image
        self.wait_and_click('//a[@class="iusc"]')
        time.sleep(1)

        elem = self.browser.find_element(By.XPATH, '//iframe[@id="OverlayIFrame"]')
        print('Scraping links')

        links = []

        for i in range(50):
            try:
                for j in range(20):
                    elem.send_keys(Keys.PAGE_DOWN)
                    time.sleep(0.2)

                self.browser.switch_to.frame(elem)

                imgs = self.browser.find_elements(By.XPATH, '//a[@class="richImgLnk"]')
                print('iframe links {}'.format(len(imgs)))

                for img in imgs:
                    try:
                        attr_m = img.get_attribute("data-m")
                        if attr_m:
                            json_m = json.loads(attr_m)
                            links.append(json_m['murl'])
                    except Exception as e:
                        print('[Exception occurred while collecting links from bing_full] {}'.format(e))

                time.sleep(1)

                self.browser.switch_to.default_content()
                elem.send_keys(Keys.ARROW_RIGHT)
            except StaleElementReferenceException:
                # print('[Expected Exception - StaleElementReferenceException]')
                pass
            except Exception as e:
                print('[Exception occurred while collecting links from bing_full] {}'.format(e))

        links = self.remove_duplicates(links)

        print('Collect links done. Site: {}, Keyword: {}, Total: {}'.format('bing_full', keyword, len(links)))
        self.browser.close()

        filter = LinkFilter()
        filtered_links = filter.filter_links(links)
        return filtered_links

    def pexels_full(self, keyword, add_url="", limit=100):
        return self.pexels(keyword, add_url=add_url)

    def is_scroll_end(self):
        scroll_info = self.browser.execute_script(
            "return {"
            "    scrollTop: document.documentElement.scrollTop || document.body.scrollTop,"
            "    clientHeight: document.documentElement.clientHeight || window.innerHeight,"
            "    scrollHeight: document.documentElement.scrollHeight || document.body.scrollHeight"
            "};"
        )
        # 判断是否到底部
        is_scroll_end = scroll_info['scrollTop'] + scroll_info['clientHeight'] >= scroll_info['scrollHeight']
        return is_scroll_end

    def is_subdomain(self, url, root_domain):
        try:
            # 解析 URL
            parsed_url = urlparse(url)
            hostname = parsed_url.hostname
            # 检查是否以指定的根域名结尾
            return hostname.endswith(f".{root_domain}") or hostname == root_domain
        except Exception as e:
            print(f"解析 URL 出错: {e}")
            return False

if __name__ == '__main__':
    collect = CollectLinks()
    links = collect.pexels('People watching phone screen')
    print(len(links), links)
