import requests
from bs4 import BeautifulSoup


# done
def google(s):
    links = []
    text = []
    USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.83 Safari/537.36'
    headers = {"user-agent": USER_AGENT}
    r = requests.get("https://www.google.com/search?q=" + s, headers=headers)
    soup = BeautifulSoup(r.content, "html.parser")
    for g in soup.find_all('div', class_='yuRUbf'):
        a = g.find('a')
        t = g.find('h3')
        links.append(a.get('href'))
        text.append(t.text)
    return links, text


# Somethime request.code == 500
def yahoo(s):
    links = []
    text = []
    url = "https://search.yahoo.com/search?q=" + s + "&n=" + str(10)
    raw_page = requests.get(url)
    print(raw_page)
    soup = BeautifulSoup(raw_page.text, "html.parser")
    for link in soup.find_all(attrs={"class": "ac-algo fz-l ac-21th lh-24"}):
        links.append(link.get('href'))
        text.append(link.text)
    return links, text


# done
def duck(s):
    links = []
    text = []
    userAgent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.83 Safari/537.36'
    headers = {'user-agent': userAgent}
    r = requests.get('https://duckduckgo.com/html/?q=' + s, headers=headers)
    s = BeautifulSoup(r.content, "html.parser")
    for i in s.find_all('div', attrs={'class': 'results_links_deep'}):
        a = i.find('a', attrs={'class': 'result__a'})
        links.append(a.get('href'))
        text.append(a.text)
    links.pop(0)
    text.pop(0)
    return links, text


# done
def ecosia(s):
    links = []
    text = []
    userAgent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.83 Safari/537.36'
    headers = {'user-agent': userAgent}
    r = requests.get('https://www.ecosia.org/search?q=' + s, headers=headers)
    soup = BeautifulSoup(r.text, "html.parser")
    for i in soup.find_all("h2", attrs={'class': 'result-firstline-title'}):
        a = i.find("a", attrs={'class': 'js-result-title'})
        text.append(a.text)
        links.append(a.get('href'))
    return links, text

def bing(search):
    userAgent = ('Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.111 Safari/537.36')
    headers = {'user-agent' : userAgent}
    URL = ('https://www.bing.com/search?q='+search)
    request = requests.get(URL, headers=headers)

    soup = BeautifulSoup(request.content, "html.parser")
    results = []
    texts = []

    for i in soup.find_all('li', {'class' : 'b_algo'}):
        link = i.find_all('a')
        link_text = i.find('a')
        links = link[0]['href']
        results.append(links)
        texts.append(link_text.text)

    return(results, texts)

def givewater(search):
    userAgent = ('Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.111 Safari/537.36')
    URL = ('https://search.givewater.com/serp?q='+search)
    headers = {'user-agent' : userAgent}
    request = requests.get(URL, headers=headers)
    
    soup = BeautifulSoup(request.content, 'html.parser')
    results = []
    texts = []

    for i in soup.find_all('div', {'class' : 'web-bing__result'}):
        link = i.find_all('a')
        link_text = i.find('a')
        links = link[0]['href']
        results.append(links)
        texts.append(link_text.text)
    
    return(results, texts)