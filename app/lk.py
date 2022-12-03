from . import BaseExtractor

class Lk21(BaseExtractor):
    tag = "movie"
    host = "https://lk21official.info"
    url = "https://dl.indexmovies.xyz/get/"

    def extract_meta(self, id: str) -> dict:
        """
        Ambil semua metadata dari halaman web

        Args:
              id: type 'str'
        """

        raw = self.session.get(f"{self.host}/{id}")
        soup = self.soup(raw)

        img = soup.find(class_="img-thumbnail")

        meta = self.MetaSet()
        meta["judul"] = img["alt"]
        meta["image"] = "https:" + img["src"]

        content = soup.find(class_="content")
        for div in content.findAll("div"):
            if (k := div.h2) and (k := k.text) and k not in ["Oleh", "Diunggah"]:
                value = ", ".join(h3.text for h3 in div.findAll("h3"))
                meta.add(k, value, split=k not in ["Imdb", "Diterbitkan"])
        if (block := soup.find("blockquote")):
            block.strong.decompose()
            block.span.decompose()

            meta["sinopsis"] = block.text

        return meta

    def extract_data(self, id: str) -> dict:
        #cookie_data = cookie.get_cookie(id)
        raw = self.session.post("https://dl.indexmovies.xyz/verifying.php",
                                headers={
                                    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                                    "Accept": "*/*",
                                    "X-Requested-With": "XMLHttpRequest",
                                    #"user-agent" : "Mozilla/5.0 (Linux; Android 12;CPH2043) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Mobile Safari/537.36",
                                    "cookie" : self.get_cookie(id)
                                },
                                params={"slug": id},
                                data={"slug": id}
                                )
        soup = self.soup(raw)
        #print(soup)
        tb = soup.find("tbody")

        result = {}
        for tr in tb.findAll("tr"):
            title = tr.find("strong").text
            result[title] = {}
            for td in tr.findAll("td")[1:]:
                if (a := td.a):
                    result[title][a["class"]
                                  [-1].split("-")[-1]] = a["href"]
        return result

    def search(self, query: str, page: int = 1) -> list:
        """
        Cari item berdasarkan 'query' yang diberikan

        Args:
              query: kata kunci pencarian, type 'str'
              page: indeks halaman web, type 'int'
        """

        raw = self.session.get(self.host,
                               params={"s": query})

        soup = self.soup(raw)

        r = []
        for item in soup.findAll(class_="search-item"):
            a = item.a
            tag = item.find(class_='cat-links').findAll('a')[0].get('href')
            thumb = 'https://' + item.find(class_='img-thumbnail').get('src')[5:]
            extra = {"genre": [], "star": [], "country": [],
                     "size": [""], "quality": [""], "year": [""], 
                     "tag": [], 
                     "thumb" : []}
            
            for p in filter(lambda x: x.strong is not None, item.findAll("p")):
                np, vl = self.re.findall(
                    r"^([^:]+):\s+(.+)", p.text.strip())[0]
                np = "star" if np == "Bintang" else "director" if np == "Sutradara" else np
                extra[np] = self.re.split(r"\s*,\s*", vl) if "," in vl else vl

            extra["id"] = self.re.search(
                r"\w/([^/]+)", a["href"]).group(1)
            extra["tag"] = "series" if tag.find("series")!=-1 else "movie"
            extra["thumb"] = thumb
            result = {
                "title": (item.find("h2").text or a.img["alt"]).strip(),
            }
            result.update(extra)
            if tag.find("series")==-1:
              r.append(result)
        return r


    def get_cookie(self, id):
      url = "https://dl.indexmovies.xyz/get/"
      print(url+id)
      req = self.session.get(url+id)
      req = req.text
      search = req.find("setCookie('validate'")
      print("validate="+req[search+23: search+63])
      return "validate="+req[search+23: search+63]
