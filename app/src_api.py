from app.lk import Lk21 as Layarkaca21
from app.bypasser import Bypass
import json
import app

def resjson(data):
    return json.dumps(data, indent=4, sort_keys=True)

scraper = Layarkaca21()
#search
def search(name):
    result = scraper.search(name)
    print(len(result))
    return result

#show
def show(id):
    return scraper.extract(id)

def download(url):
    bypasser = Bypass()
    return bypasser.bypass_url(url)

