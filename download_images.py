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

import argparse
import base64
import imghdr
import os
import shutil
import signal
from multiprocessing import Pool
from pathlib import Path

import requests


class Sites:
    GOOGLE = 1
    NAVER = 2
    GOOGLE_FULL = 3
    NAVER_FULL = 4
    BING = 5
    BING_FULL = 6
    PEXELS = 7
    PEXELS_FULL = 8

    @staticmethod
    def get_text(code):
        if code == Sites.GOOGLE:
            return 'google'
        elif code == Sites.NAVER:
            return 'naver'
        elif code == Sites.GOOGLE_FULL:
            return 'google'
        elif code == Sites.NAVER_FULL:
            return 'naver'
        elif code == Sites.BING:
            return 'bing'
        elif code == Sites.BING_FULL:
            return 'bing'
        elif code == Sites.PEXELS:
            return 'pexels'
        elif code == Sites.PEXELS_FULL:
            return 'pexels'

    @staticmethod
    def get_face_url(code):
        if code == Sites.GOOGLE or Sites.GOOGLE_FULL:
            return "&tbs=itp:face"
        if code == Sites.NAVER or Sites.NAVER_FULL:
            return "&face=1"
        if code == Sites.BING or Sites.BING_FULL:
            return ""
        if code == Sites.PEXELS or Sites.PEXELS_FULL:
            return ""


class AutoCrawler:
    def __init__(self, skip_already_exist=True, n_threads=8, do_google=True, do_naver=True, do_bing=True,
                 do_pexels=True, download_path='download',
                 full_resolution=False, face=False, no_gui=False, limit=0, proxy_list=None):
        """
        :param skip_already_exist: Skips keyword already downloaded before. This is needed when re-downloading.
        :param n_threads: Number of threads to download.
        :param do_google: Download from google.com (boolean)
        :param do_naver: Download from naver.com (boolean)
        :param download_path: Download folder path
        :param full_resolution: Download full resolution image instead of thumbnails (slow)
        :param face: Face search mode
        :param no_gui: No GUI mode. Acceleration for full_resolution mode.
        :param limit: Maximum count of images to download. (0: infinite)
        :param proxy_list: The proxy list. Every thread will randomly choose one from the list.
        """

        self.skip = skip_already_exist
        self.n_threads = n_threads
        self.do_google = do_google
        self.do_naver = do_naver
        self.do_bing = do_bing
        self.do_pexels = do_pexels
        self.download_path = download_path
        self.full_resolution = full_resolution
        self.face = face
        self.no_gui = no_gui
        self.limit = limit
        self.proxy_list = proxy_list if proxy_list and len(proxy_list) > 0 else None

        os.makedirs('./{}'.format(self.download_path), exist_ok=True)

    @staticmethod
    def all_dirs(path):
        paths = []
        for dir in os.listdir(path):
            if os.path.isdir(path + '/' + dir):
                paths.append(path + '/' + dir)

        return paths

    @staticmethod
    def all_files(path):
        paths = []
        for root, dirs, files in os.walk(path):
            for file in files:
                if os.path.isfile(path + '/' + file):
                    paths.append(path + '/' + file)

        return paths

    @staticmethod
    def get_extension_from_link(link, default='jpg'):
        splits = str(link).split('.')
        if len(splits) == 0:
            return default
        ext = splits[-1].lower()
        if ext == 'jpg' or ext == 'jpeg':
            return 'jpg'
        elif ext == 'gif':
            return 'gif'
        elif ext == 'png':
            return 'png'
        else:
            return default

    @staticmethod
    def validate_image(path):
        ext = imghdr.what(path)
        if ext == 'jpeg':
            ext = 'jpg'
        return ext  # returns None if not valid

    @staticmethod
    def make_dir(dirname):
        current_path = os.getcwd()
        path = os.path.join(current_path, dirname)
        if not os.path.exists(path):
            os.makedirs(path)

    @staticmethod
    def get_keywords(keywords_file='datasets_keywords\{}.txt', site_name='all'):
        # read search keywords from file
        with open(keywords_file.format(site_name), 'r', encoding='utf-8-sig') as f:
            text = f.read()
            lines = text.split('\n')
            lines = filter(lambda x: x != '' and x is not None, lines)
            keywords = sorted(set(lines))

        print('{} keywords found: {}'.format(len(keywords), keywords))

        # re-save sorted keywords
        # with open(keywords_file, 'w+', encoding='utf-8') as f:
        #    for keyword in keywords:
        #        f.write('{}\n'.format(keyword))

        return keywords

    @staticmethod
    def save_object_to_file(object, file_path, is_base64=False):
        try:
            with open('{}'.format(file_path), 'wb') as file:
                if is_base64:
                    file.write(object)
                else:
                    shutil.copyfileobj(object.raw, file)
        except Exception as e:
            print('Save failed - {}'.format(e))

    @staticmethod
    def base64_to_object(src):
        header, encoded = str(src).split(',', 1)
        data = base64.decodebytes(bytes(encoded, encoding='utf-8'))
        return data

    def download_images(self, keyword, links, site_name, max_count=0):
        self.make_dir(
            '{}/images_file/{}/{}'.format(self.download_path, site_name, keyword.replace('"', '').replace(' ', '_').replace('-', '_')))
        total = len(links)
        success_count = 0

        if max_count == 0:
            max_count = total

        for index, link in enumerate(links):
            if success_count >= max_count:
                break

            try:
                print('Downloading {} from {}: {} / {}'.format(keyword, site_name, success_count + 1, max_count))

                if str(link).startswith('data:image/jpeg;base64'):
                    response = self.base64_to_object(link)
                    ext = 'jpg'
                    is_base64 = True
                elif str(link).startswith('data:image/png;base64'):
                    response = self.base64_to_object(link)
                    ext = 'png'
                    is_base64 = True
                else:
                    response = requests.get(link, stream=True, timeout=10)
                    ext = self.get_extension_from_link(link)
                    is_base64 = False

                no_ext_path = '{}/images_file/{}/{}/{}_{}_{}'.format(self.download_path.replace('"', ''), site_name,
                                                                     keyword.replace('"', '').replace(' ', '_').replace('-', '_'),
                                                                     site_name,
                                                                     keyword.replace('"', '').replace(' ', '_').replace('-', '_'),
                                                                     str(index).zfill(4))
                path = no_ext_path + '.' + ext
                self.save_object_to_file(response, path, is_base64=is_base64)

                success_count += 1
                del response

                ext2 = self.validate_image(path)
                if ext2 is None:
                    print('Unreadable file - {}'.format(link))
                    os.remove(path)
                    success_count -= 1
                else:
                    if ext != ext2:
                        path2 = no_ext_path + '.' + ext2
                        os.rename(path, path2)
                        print('Renamed extension {} -> {}'.format(ext, ext2))

            except KeyboardInterrupt:
                break

            except Exception as e:
                print('Download failed - ', e)
                continue

    def download_from_site(self, keyword, site_code):
        site_name = Sites.get_text(site_code)

        try:
            print('Collecting links... {} from {}'.format(keyword, site_name))

            print('Downloading images from collected links... {} from {}'.format(keyword, site_name))
            txt_file_path = '{}/{}/{}/{}.txt'.format(self.download_path, 'images_url', site_name,
                                                     keyword.replace('"', '').replace(' ', '_'))
            # 确保文件夹路径存在
            os.makedirs(os.path.dirname(txt_file_path), exist_ok=True)
            with open(txt_file_path.format(site_name), 'r', encoding='utf-8-sig') as f:
                text = f.read()
                lines = text.split('\n')
                lines = filter(lambda x: x != '' and x is not None, lines)
                links = sorted(set(lines))

            print('Downloading images from collected links... {} from {}'.format(keyword, site_name))
            self.download_images(keyword, links, site_name, max_count=self.limit)
            Path('{}/{}/{}_done'.format(self.download_path, keyword.replace('"', ''), site_name)).touch()

            print('Done write image url  {} : {}'.format(site_name, keyword))

        except Exception as e:
            print('Exception {}:{} - {}'.format(site_name, keyword, e))
            return

    def download(self, args):
        self.download_from_site(keyword=args[0], site_code=args[1])

    def init_worker(self):
        signal.signal(signal.SIGINT, signal.SIG_IGN)

    def do_crawling(self):
        tasks = []

        site_name = Sites.get_text(Sites.GOOGLE)
        keywords = self.get_keywords(site_name=site_name)
        if keywords:
            for keyword in keywords:
                dir_name = '{}/images_file/{}/{}'.format(self.download_path, site_name, keyword)
                google_done = os.path.exists(os.path.join(os.getcwd(), dir_name, 'google_done'))
                if google_done and self.skip:
                    print('Skipping done task {}'.format(dir_name))
                    continue

                if self.do_google and not google_done:
                    if self.full_resolution:
                        tasks.append([keyword, Sites.GOOGLE_FULL])
                    else:
                        tasks.append([keyword, Sites.GOOGLE])

        site_name = Sites.get_text(Sites.BING)
        keywords = self.get_keywords(site_name=site_name)
        if keywords:
            for keyword in keywords:
                dir_name = '{}/images_file/{}/{}'.format(self.download_path, site_name, keyword)
                bing_done = os.path.exists(os.path.join(os.getcwd(), dir_name, 'bing_done'))
                if bing_done and self.skip:
                    print('Skipping done task {}'.format(dir_name))
                    continue

                if self.do_bing and not bing_done:
                    if self.full_resolution:
                        tasks.append([keyword, Sites.BING_FULL])
                    else:
                        tasks.append([keyword, Sites.BING])

        site_name = Sites.get_text(Sites.PEXELS)
        keywords = self.get_keywords(site_name=site_name)
        if keywords:
            for keyword in keywords:
                dir_name = '{}/images_file/{}/{}'.format(self.download_path, site_name, keyword)
                pexels_done = os.path.exists(os.path.join(os.getcwd(), dir_name, 'pexels_done'))
                if pexels_done and self.skip:
                    print('Skipping done task {}'.format(dir_name))
                    continue

                if self.do_pexels and not pexels_done:
                    if self.full_resolution:
                        tasks.append([keyword, Sites.PEXELS_FULL])
                    else:
                        tasks.append([keyword, Sites.PEXELS])

        site_name = Sites.get_text(Sites.NAVER)
        keywords = self.get_keywords(site_name=site_name)
        if keywords:
            for keyword in keywords:
                dir_name = '{}/images_file/{}/{}'.format(self.download_path, site_name, keyword)
                naver_done = os.path.exists(os.path.join(os.getcwd(), dir_name, 'naver_done'))
                if naver_done and self.skip:
                    print('Skipping done task {}'.format(dir_name))
                    continue

                if self.do_naver and not naver_done:
                    if self.full_resolution:
                        tasks.append([keyword, Sites.NAVER_FULL])
                    else:
                        tasks.append([keyword, Sites.NAVER])

        try:
            pool = Pool(self.n_threads, initializer=self.init_worker)
            pool.map(self.download, tasks)
        except KeyboardInterrupt:
            pool.terminate()
            pool.join()
        else:
            pool.terminate()
            pool.join()
        print('Task ended. Pool join.')

        print('End Program')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--skip', type=str, default='true',
                        help='Skips keyword already downloaded before. This is needed when re-downloading.')
    parser.add_argument('--threads', type=int, default=4, help='Number of threads to download.')
    parser.add_argument('--google', type=str, default='true', help='Download from google.com (boolean)')
    parser.add_argument('--naver', type=str, default='true', help='Download from naver.com (boolean)')
    parser.add_argument('--bing', type=str, default='true', help='Download from bing.com (boolean)')
    parser.add_argument('--pexels', type=str, default='true', help='Download from pexels.com (boolean)')
    parser.add_argument('--full', type=str, default='false',
                        help='Download full resolution image instead of thumbnails (slow)')
    parser.add_argument('--face', type=str, default='false', help='Face search mode')
    parser.add_argument('--no_gui', type=str, default='auto',
                        help='No GUI mode. Acceleration for full_resolution mode. '
                             'But unstable on thumbnail mode. '
                             'Default: "auto" - false if full=false, true if full=true')
    parser.add_argument('--limit', type=int, default=0,
                        help='Maximum count of images to download per site.')
    parser.add_argument('--proxy-list', type=str, default='',
                        help='The comma separated proxy list like: "socks://127.0.0.1:1080,http://127.0.0.1:1081". '
                             'Every thread will randomly choose one from the list.')
    args = parser.parse_args()

    _skip = False if str(args.skip).lower() == 'false' else True
    _threads = args.threads
    _google = False if str(args.google).lower() == 'false' else True
    _naver = False if str(args.naver).lower() == 'false' else True
    _bing = False if str(args.bing).lower() == 'false' else True
    _pexels = False if str(args.pexels).lower() == 'false' else True
    _full = False if str(args.full).lower() == 'false' else True
    _face = False if str(args.face).lower() == 'false' else True
    _limit = int(args.limit)
    _proxy_list = args.proxy_list.split(',')

    no_gui_input = str(args.no_gui).lower()
    if no_gui_input == 'auto':
        _no_gui = _full
    elif no_gui_input == 'true':
        _no_gui = True
    else:
        _no_gui = False

    print(
        'Options - skip:{}, threads:{}, google:{}, naver:{},  bing:{},  pexels:{}, full_resolution:{}, face:{}, no_gui:{}, limit:{}, _proxy_list:{}'
        .format(_skip, _threads, _google, _naver, _bing, _pexels, _full, _face, _no_gui, _limit, _proxy_list))

    crawler = AutoCrawler(skip_already_exist=_skip, n_threads=_threads,
                          do_google=_google, do_naver=_naver, do_bing=_bing, do_pexels=_pexels, full_resolution=_full,
                          face=_face, no_gui=_no_gui, limit=_limit, proxy_list=_proxy_list)
    crawler.do_crawling()
