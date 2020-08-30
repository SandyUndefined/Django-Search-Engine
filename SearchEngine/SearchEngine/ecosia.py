import requests
import urllib.parse
from bs4 import BeautifulSoup
s = input("Search here...")
userAgent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.83 Safari/537.36'
headers = {'user-agent' : userAgent}
r = requests.get('https://www.ecosia.org/search?q='+s,headers=headers)
soup = BeautifulSoup(r.text, "html.parser")
for i in soup.find_all("h2", attrs={'class':'result-firstline-title'}):
    a = i.find("a",attrs={'class':'js-result-title'})
    print(a.text)
    print(a.get('href'))
