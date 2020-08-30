import requests
from bs4 import BeautifulSoup


#done
def google(s):
    results = []
    USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.83 Safari/537.36'
    headers = {"user-agent": USER_AGENT}
    r = requests.get("https://www.google.com/search?q=" +s, headers=headers)
    soup = BeautifulSoup(r.content, "html.parser")
    for g in soup.find_all('div', class_='r'):
        a = g.find('a')
        results.append(a.get('href'))
    return results


#done
def yahoo(s):
    result = []
    url = "https://search.yahoo.com/search?q=" +s+ "&n=" + str(10)
    raw_page = requests.get(url)
    soup = BeautifulSoup(raw_page.text, "html.parser")
    for link in soup.find_all(attrs={"class": "ac-algo fz-l ac-21th lh-24"}):
        result.append(link.get('href'))
    return result


#done
def duck(s):
    results = []
    userAgent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.83 Safari/537.36'
    headers = {'user-agent': userAgent}
    r = requests.get('https://duckduckgo.com/html/?q=' + s, headers=headers)
    s = BeautifulSoup(r.content, "html.parser")
    for i in s.find_all('div', attrs={'class': 'results_links_deep'}):
        a = i.find('a',attrs={'class': 'result__a'})
        results.append(a.get('href'))
    results.pop(0)
    return results


#done
def ecosia(s):
    results = []
    userAgent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.83 Safari/537.36'
    headers = {'user-agent': userAgent}
    r = requests.get('https://www.ecosia.org/search?q=' + s, headers=headers)
    soup = BeautifulSoup(r.text, "html.parser")
    for i in soup.find_all("h2", attrs={'class': 'result-firstline-title'}):
        a = i.find("a", attrs={'class': 'js-result-title'})
        #print(a.text)
        results.append(a.get('href'))
    return results