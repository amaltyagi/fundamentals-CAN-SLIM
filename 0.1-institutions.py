import csv
import requests
from bs4 import BeautifulSoup

file = 'sp500-3.csv'

with open(file) as f:
    reader = csv.reader(f)
    listings = [row[0] for row in reader if row[0].isalpha()]

ticker = listings[0]

for ticker in listings:
    try:
        inside_url = 'https://money.cnn.com/quote/shareholders/shareholders.html?symb='+ticker+'&subView=insider'
        soup = BeautifulSoup(requests.get(inside_url).content, 'html.parser')
        inside_img = 'https:' + soup.find('div', attrs={'id':'wsod_companyChart'}).find('img')['src']
        r = requests.get(inside_img)
        with open('img/'+ticker+'_inside.png', 'wb') as f:
            f.write(r.content)
    except:
        pass

    try:
        instit_url = 'https://money.cnn.com/quote/shareholders/shareholders.html?symb='+ticker+'&subView=institutional'
        soup = BeautifulSoup(requests.get(instit_url).content, 'html.parser')
        instit_img = 'https:' + soup.find('div', attrs={'id':'wsod_topInstitutionalTransactions'}).find_all('img')[1]['src']
        r = requests.get(instit_img)
        with open('img/'+ticker+'_instit.png', 'wb') as f:
            f.write(r.content)
    except:
        pass
    
