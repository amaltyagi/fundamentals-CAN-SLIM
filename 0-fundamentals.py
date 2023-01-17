import warnings
warnings.simplefilter("ignore", UserWarning)

import csv
import requests
from bs4 import BeautifulSoup
from urllib3 import exceptions
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
#from selenium.webdriver.support.ui import Select
#from webdriver_manager.firefox import GeckoDriverManager
import sys, os
import time, datetime

file = 'data/nasdaq-listed.csv'

with open(file) as f:
    reader = csv.reader(f)
    listings = [row[0] for row in reader if row[0].isalpha()]

fundamentals = [['Ticker','Industry','Sector','Fiscal_Year_End','ROE','Annual_EPS','Annual_EPS_Growth','Annual_Net_Income_Growth','Annual_Basic_Shares_Outstanding','Annual_Sales_Growth','Quarter_EPS','Quarter_EPS_Growth','Quarter_Net_Income_Growth','Quarter_Net_Margin','Quarter_Sales_Growth','Total_Shareholders_Equity','Liabilities_&_Shareholders_Equity','Net_Operating_Cash_Flow']]

options = Options()
options.add_argument("--headless")
driver = webdriver.Chrome(options=options)

"""
fireFoxOptions = webdriver.FirefoxOptions()
fireFoxOptions.add_argument('--headless')
driver = webdriver.Firefox(service=webdriver.firefox.service.Service(GeckoDriverManager().install()))
"""

def scrape(tickers=listings):
    failed_tickers = []
    
    for ticker in tickers:
        print(ticker)
        curr_fundamentals = [ticker]
        
        try: # If error thrown on any site, we'll try again for this ticker later
            
            # First, we get basic info from Fox Business--Industry, Sector, Fiscal_Year_End, and ROE
            driver.get('https://www.foxbusiness.com/quote?stockTicker='+ticker+'#profile')
            time.sleep(2)
            soup = BeautifulSoup(driver.page_source, 'html.parser', from_encoding='utf-8')
            glance = soup.find('div', attrs={'class':'glance'}).find('table')
            t = glance.text
            s = 'Industry '
            t = t[t.index(s)+len(s):]
            industry = t[:t.index('  ')]
            s = 'Sector '
            t = t[t.index(s)+len(s):]
            sector = t[:t.index('  ')]
            s = 'Fiscal Year-end '
            t = t[t.index(s)+len(s):]
            year_end = t[:t.index('  ')].replace(' / ','/')
            profitability = soup.find('div', attrs={'class':'column-2'}).find('div', attrs={'class':'table'})
            t = profitability.text
            t = t[t.index('Return on Equity ')+len('Return on Equity '):]
            roe = t[:t.index('R')]
            
            print('Industry: '+industry)
            print('Sector: '+sector)
            print('Fiscal_Year_End: '+year_end)
            print('ROE: '+roe)
            curr_fundamentals.append(industry)
            curr_fundamentals.append(sector)
            curr_fundamentals.append(year_end)
            curr_fundamentals.append(roe)

            # Wall Street Journal has a cleaner site, so we access our financial (P&L, balance sheet, & cash flow) statements here
            driver.get('https://www.wsj.com/market-data/quotes/'+ticker+'/financials/annual/income-statement')
            time.sleep(2)
            soup = BeautifulSoup(driver.page_source, 'html.parser', from_encoding='utf-8')
            income = soup.find('table', attrs={'class':'cr_dataTable'})
            t = income.text.replace(',','')
            t = t[t.index('Sales/Revenue'):].replace('   ','  ')
            li = t.split('           ')
            stats = ['EPS (Basic)', 'Net Income Growth', 'Basic Shares Outstanding', 'Sales Growth']
            for s in stats:
                for elem in li:
                    if elem.lstrip().startswith(s):
                        print('Annual_'+s.replace(' ','_')+': '+elem.replace(s,'').replace('Growth','').lstrip())
                        curr_fundamentals.append(elem.replace(s,'').replace('Growth','').lstrip())
            driver.get('https://www.wsj.com/market-data/quotes/'+ticker+'/financials/quarter/income-statement')
            time.sleep(2)
            soup = BeautifulSoup(driver.page_source, 'html.parser', from_encoding='utf-8')
            income = soup.find('table', attrs={'class':'cr_dataTable'})
            t = income.text.replace(',','')
            t = t[t.index('Sales/Revenue'):].replace('   ','  ')
            li = t.split('           ')
            stats = ['EPS (Basic)', 'Net Income Growth', 'Net Margin', 'Sales Growth']
            for s in stats:
                for elem in li:
                    if elem.lstrip().startswith(s):
                        print('Quarter_'+s.replace(' ','_')+': '+elem.replace(s,'').replace('Growth','').lstrip())
                        curr_fundamentals.append(elem.replace(s,'').replace('Growth','').lstrip())

            try:
                tmp_fundamentals = []   
                balance_stats = ["Total Shareholders' Equity", "Liabilities & Shareholders' Equity"]
                driver.get('https://www.wsj.com/market-data/quotes/'+ticker+'/financials/annual/balance-sheet')
                time.sleep(2)
                soup = BeautifulSoup(driver.page_source, 'html.parser', from_encoding='utf-8')
                balance = soup.find('div', attrs={'class':'collapsed'})#.find('table', attrs={'class':'cr_dataTable'})
                t = balance.text.replace(',','')
                t = t[t.index('ST Debt'):].replace('   ','  ')
                li = t.split('           ')
                for s in balance_stats:
                    for elem in li:
                        if elem.lstrip().startswith(s) and 'Assets' not in elem:
                            print(s.replace(' ','_')+': '+elem.replace(s,'').lstrip())
                            tmp_fundamentals.append(elem.replace(s,'').lstrip())
                
                assert len(balance_stats) == len(tmp_fundamentals)
                for s in tmp_fundamentals:
                    curr_fundamentals.append(s)

            except:
                for s in range(len(balance_stats)):
                    curr_fundamentals.append('')

            try:
                tmp_fundamentals = []  
                cash_stats = ['Net Operating Cash Flow']
                driver.get('https://www.wsj.com/market-data/quotes/'+ticker+'/financials/annual/cash-flow')
                time.sleep(2)
                soup = BeautifulSoup(driver.page_source, 'html.parser', from_encoding='utf-8')
                cashflow = soup.find('table', attrs={'class':'cr_dataTable'})
                t = cashflow.text.replace(',','')
                t = t[t.index('Net Income before Extraordinaries'):].replace('   ','  ')
                li = t.split('           ')
                for s in cash_stats:
                    for elem in li:
                        if elem.lstrip().startswith(s) and 'Growth' not in elem and 'Sales' not in elem:
                            print(s.replace(' ','_')+': '+elem.replace(s,'').lstrip())
                            tmp_fundamentals.append(elem.replace(s,'').lstrip())

                assert len(cash_stats) == len(tmp_fundamentals)
                for s in tmp_fundamentals:
                    curr_fundamentals.append(s)
            
            except:
                for s in range(len(cash_stats)):
                    curr_fundamentals.append('')
                

            """
            # Finally, CNN has several lists regarding insider & institutional investments.
            # Selenium (the following code) isn't necessary for scraping these images...check out the next Python file
            driver.get('https://money.cnn.com/quote/shareholders/shareholders.html?symb='+ticker+'&subView=insider')
            time.sleep(2)
            soup = BeautifulSoup(driver.page_source, 'html.parser', from_encoding='utf-8')
            insider = soup.find('table', attrs={'id', 'wsod_insiderTrading'})
            
            #driver.get('https://money.cnn.com/quote/shareholders/shareholders.html?symb='+ticker+'&subView=institutional')
            """

            fundamentals.append(curr_fundamentals)

            for f in os.listdir():
                if f.endswith('incomplete.csv'):
                    os.remove(f)

            s = str(datetime.datetime.now())
            s = s[:s.index(' ')]
            with open('fundamentals_'+s+'_incomplete.csv', 'w') as f:
                writer = csv.writer(f)
                writer.writerows(fundamentals)
            
        except KeyboardInterrupt: # End data collection
            driver.close()
            print('\n'+'Failed: '+str(failed_tickers))
            sys.exit(0)
        """
        except: # Store ticker and move onto the next
            failed_tickers.append(ticker)
        """ 
        print('\n')
        
    if failed_tickers == [] or len(failed_tickers) == len(tickers): # No improvement since last iteration => End data collection
        print('\n'+'Failed: '+str(failed_tickers))
        s = str(datetime.datetime.now())
        s = s[:s.index(' ')]
        with open('fundamentals_'+s+'.csv', 'w') as f:
            writer = csv.writer(f)
            writer.writerows(fundamentals)
        return failed_tickers

    print('\n'+'Failed: '+str(failed_tickers)) # Some tickers failed => Try again!
    return scrape(failed_tickers)

scrape()
