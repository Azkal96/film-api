from urllib.parse import urlparse
from http.cookiejar import LWPCookieJar
import requests
import requests_cache
import bs4
import re
import sys
import glob
import os
import importlib
import logging
from collections import UserDict

from flask import Flask



class BaseExtractorError(Exception):
    pass


requests_cache.install_cache(cache_name=os.path.expanduser(
    '~/.lk21-requests-cache'), backend='sqlite', expire_after=90)


class BaseExtractor:
    def __init__(self, logger=None, args=None):
        """
        Induk dari semua 'extractor'

        Args:
              logger: logger instance
              args: 'argparse.Namespace'
        """

        self.session = self._build_session()
        self.re = re
        self.logger = logger or logging
        self.args = args
        self.counter = 0
        self.run_as_module = True

        self.MetaSet = MetaSet

    def _build_session(self) -> requests.Session:
        """
        Buat session baru
        """

        session = requests.Session()
        session.headers[
            "User-Agent"] = "Mozilla/5.0 (Linux; Android 7.0; 5060 Build/NRD90M; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/58.0.3029.83 Mobile Safari/537.36"
        session.cookies = LWPCookieJar()
        return session

    def setProxies(self, proxy: str) -> None:
        if not proxy:
            return
        if self.logger:
            self.logger.info(f"Menyetel proxy: {proxy}")
        self.session.proxies = {
            "http": f"http://{proxy}",
            "https": f"https://{proxy}",
        }

    def prepare(self):
        """
        ubah :self: sebelum membuat permintaan
        """

        pass

    def dict_to_list(self, d: dict) -> list:
        """
        undocumented
        """

        prefix = self.re.compile(r"^(?:re\:|{})".format(self.host))
        if not self.run_as_module:
            return d
        list_ = []
        for k, v in d.items():
            if isinstance(v, dict):
                v = self.dict_to_list(v)
            elif isinstance(v, str) and prefix.search(v):
                id = prefix.sub("", v).strip("/")
                if self.args and (self.args.json or self.args.json_dump):
                    if self.logger:
                        self.logger.info(f"Mengekstrak link unduhan: {id}")
                    data = self.extract_data(id)
                    if len(data) == 1:
                        data = list(data.values())[0]
                    v = self.dict_to_list(data)
                else:
                    v = self.host + "/" + id
            list_.append({
                "key": k.strip(),
                "value": v
            })
        return list_

    def extract_meta(self, id: str) -> dict:
        """
        Ambil semua metadata dari halaman web

        Args:
              id: type 'str'
        """

        return {}

    def extract_data(self, id: str) -> dict:
        """
        Ambil semua situs unduhan dari halaman web

        Args:
              id: jalur url dimulai setelah host, type 'str'
        """

        return {}

    def filterNonetypeDict(self, items: list, keys: tuple) -> list:
        """
        undocumented
        """

        filtered = []
        for item in items:
            if all(item.get(k) not in [None, ""] for k in keys):
                filtered.append(item)
        return filtered

    def extract(self, id: any) -> dict:
        """
        Args:
            id: type 'dict' or 'str'
        """

        if isinstance(id, dict):
            if not id.get("id"):
                raise BaseExtractorError("You must provide a `id` value")
            id = id["id"]

        result = {}
        meta = self.extract_meta(id)
        result["metadata"] = meta.store if isinstance(
            meta, self.MetaSet) else meta
        result["download"] = self.dict_to_list(
            self.extract_data(id))

        result.update({
            "extractor": self.__class__.__name__,
            "tag": self.tag,
            "url": f"{self.host}/{id}",
            "host": self.host,
            "id": id,
        })

        return result

    def soup(self, raw: str) -> bs4.BeautifulSoup:
        """
        Ubah 'requests.Response' atau 'str' menjadi 'bs4.BeautifulSoup'

        Args:
              raw: type 'requests.Response' atau 'str'
        """

        text = raw.text if hasattr(raw, "text") else raw
        return bs4.BeautifulSoup(text, "html.parser")

    def getPath(self, url: str) -> str:
        """
        undocumented
        """

        return urlparse(url).path.strip("/")

    def _write(self, soup: bs4.BeautifulSoup, file: str = "x.html") -> None:
        """
        Args:
              soup: type 'requests.Response' atau 'str'
              file: type 'str'
        """

        if hasattr(soup, "prettify"):
            soup = soup.prettify()
        with open(file, "wb") as f:
            f.write(soup.encode())

    def _reformat(self, raw: str, add_counter: bool = True) -> str:
        """
        Reformat text
        """

        if not isinstance(raw, str) or re.match(r"^\d+\.", raw):
            return raw
        else:
            self.counter += 1
            raw = re.sub(r"^\s+|\s+$", "", raw)
            if add_counter:
                return f"{self.counter}. {raw}"
            else:
                return raw

    def info(self, *args, **kwargs):
        """
        undocumented
        """

        if self.logger and self.args and self.args.info:
            self.logger.info(*args, **kwargs)

    
class MetaSet(UserDict):
    def __init__(self, *args, **kwargs):
        self.store = dict()
        self.update(dict(*args, **kwargs))  # use the free update to set keys

        self._pattern = r"(?i){id} *: *(.+?)\n"
        self._content = ""

    def __getitem__(self, key):
        return self.store[key]

    def __setitem__(self, key, value):
        self.store[key] = value.strip() if isinstance(value, str) else value

    def __delitem__(self, key):
        del self.store[key]

    def __iter__(self):
        return iter(self.store)

    def __len__(self):
        return len(self.store)

    def __repr__(self):
        return repr(self.store)

    def register(self, pattern: str, content: str) -> None:
        """
        Menyetel pola Regex
        """

        if pattern:
            self._pattern = pattern
        if content:
            self._content = content

    def add(self, key: any, value: any, split: bool = True) -> None:
        key = re.sub(r" ", "_", key).lower()
        if isinstance(value, str):
            value = re.split(r"\s*,\s+", value
                             ) if split else [value]
        if not value:
            return
        if len(value) == 1:
            value = value[0].strip()
        if (pre := self.store.get(key)):
            if not isinstance(pre, list):
                self.store[key] = [pre]
            self.store[key].extend(
                [value] if not isinstance(value, list) else value)
        else:
            self.store[key] = value

    def setItem(self, id: str, key: str = None, split: bool = True) -> None:
        """
        Tambah item jika ditemukan
        """

        if (value := re.search(self._pattern.format(id=id), self._content)):
            self.add(key or id, value.group(1), split)

    def pop(self, key, default=None, force=False):
        if not self.store.get(key):
            return default
        else:
            return self.store.pop(key) or default

"""
basedir = os.path.dirname(__file__)
for file in glob.glob(f"{basedir}/*.py"):
    filename = os.path.basename(file)[:-3]
    if not filename.startswith("__"):
        importlib.import_module(f"lk21.extractors.{filename}")
del basedir, file, filename
"""

app = Flask(__name__)
from app import routes
app.run(host='0.0.0.0', port=8080)