import csv, datetime

with open('data/sp500_fundamentals_2023-01-08.csv') as f:
    reader = csv.reader(f)
    rows = [row for row in reader]
    lbls = rows[0]
    del rows[0]

lbls = ['Ticker','Sector','Industry','ROE > 17%','EPS Up 18% (1Y)','Sales Up 25% (1Q)','Sales Accel. (3Q)','EPS Up 25% (5Y)','Debt/Equity Down (3Y)','Cash/Shares Up 20% (vs. EPS)','Passes']
groups = {}

for row in rows:
    tmp = []

    industry, sector = row[1], row[2]
    if sector not in groups:
        groups[sector] = {}
    if industry not in groups[sector]:
        groups[sector][industry] = []
        
    tmp = [row[0], sector, industry]
    
    # True if ROE > 17
    try:
        roe = float(row[4])
        tmp.append(roe > 17)
    except:
        tmp.append('-')

    # True if Quarterly EPS has grown 18% compared to 1Y ago
    try:
        eps_past_5Q = [float(s) for s in row[10].replace('(','').replace(')','').strip().split(' ')]
        eps_change_5Q = eps_past_5Q[0] / eps_past_5Q[4] * 100
        tmp.append(eps_change_5Q > 18)
    except:
        tmp.append('-')

    # True if Quarterly Sales have grown 25% compared to 1Q ago
    try:
        sales_growth_past_4Q = [float(s) for s in row[14].replace('%','')[:-2].split(' ')]
        tmp.append(sales_growth_past_4Q[0] > 25)
    except:
        tmp.append('-')

    # True if Quarterly Sales have accelerated for last 3Q
    try:
        tmp.append(sales_growth_past_4Q[0] - sales_growth_past_4Q[1] > sales_growth_past_4Q[1] - sales_growth_past_4Q[2] )
    except:
        tmp.append('-')
        
    # True if Annual EPS has grown 25% from earliest data (4-5Y ago)
    try:
        eps_past_5Y = [float(s) for s in row[5].replace('(','').replace(')','').split(' ')]
        eps_change_5Y = eps_past_5Y[0] / eps_past_5Y[-1] * 100
        tmp.append(eps_change_5Y > 25)
    except:
        tmp.append('-')

    # True if Debt-to-Equity Ratio is decreasing for last 3Y
    try:
        shareholder_equity = [float(s) for s in row[-3].replace('(','').replace(')','').split(' ')]
        liabilities_and_equity = [float(s) for s in row[-2].replace('(','').replace(')','').split(' ')]
        liabilities = [liabilities_and_equity[i] - shareholder_equity[i] for i in range(len(shareholder_equity))]
        tmp.append(liabilities[0] / shareholder_equity[0] < liabilities[1] / shareholder_equity[1] and liabilities[1] / shareholder_equity[1] < liabilities[2] / shareholder_equity[2])
    except:
        tmp.append('-')

    # True if Annual Cash Flow / Shares > Annual EPS by at least 20%
    try:
        operating_cash_flow = row[-1].replace('(','').replace(')','')
        outstanding_shares = row[8]
        to_compare = 100 * float(operating_cash_flow[:operating_cash_flow.index(' ')]) / float(outstanding_shares[:outstanding_shares.index(' ')])
        tmp.append(to_compare > eps_past_5Y[0])
    except:
        tmp.append('-')

    pass_count = tmp.count(True)
    tmp.append(pass_count)
    
    groups[sector][industry].append(tmp)

to_write = [lbls]
for sector in groups:
    for industry in groups[sector]:
        for li in groups[sector][industry]:
            to_write.append(li)

now = str(datetime.datetime.now())
now = now[:now.index(' ')]
with open('data/fundamentals_'+now+'_by_sector.csv', 'w') as f:
    writer = csv.writer(f)
    writer.writerows(to_write)

to_write_ordered = sorted(to_write[1:], key=lambda x:(x[-1]))[::-1]
to_write_ordered.insert(0, lbls)
with open('data/fundamentals_'+now+'_by_pass.csv', 'w') as f:
    writer = csv.writer(f)
    writer.writerows(to_write_ordered)
