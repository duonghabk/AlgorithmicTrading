# ============================================================================
# Greenblatt's Magic Formula Implementation
# Author - Mayank Rasu

# Please report bugs/issues in the Q&A section
# =============================================================================


import requests
from bs4 import BeautifulSoup
import pandas as pd

tickers = ["AXP","AAPL","BA","CAT","CVX","CSCO","DIS","DOW", "XOM",
           "HD","IBM","INTC","JNJ","KO","MCD","MMM","MRK","MSFT",
           "NKE","PFE","PG","TRV","UTX","UNH","VZ","V","WMT","WBA"]

#list of tickers whose financial data needs to be extracted
financial_dir = {}

for ticker in tickers:
    try:
    #getting balance sheet data from yahoo finance for the given ticker
        temp_dir = {}
        url = 'https://in.finance.yahoo.com/quote/'+ticker+'/balance-sheet?p='+ticker
        page = requests.get(url)
        page_content = page.content
        soup = BeautifulSoup(page_content,'html.parser')
        tabl = soup.find_all("div", {"class" : "M(0) Whs(n) BdEnd Bdc($seperatorColor) D(itb)"})
        for t in tabl:
            rows = t.find_all("div", {"class" : "rw-expnded"})
            for row in rows:
                temp_dir[row.get_text(separator='|').split("|")[0]]=row.get_text(separator='|').split("|")[1]
        
        #getting income statement data from yahoo finance for the given ticker
        url = 'https://in.finance.yahoo.com/quote/'+ticker+'/financials?p='+ticker
        page = requests.get(url)
        page_content = page.content
        soup = BeautifulSoup(page_content,'html.parser')
        tabl = soup.find_all("div", {"class" : "M(0) Whs(n) BdEnd Bdc($seperatorColor) D(itb)"})
        for t in tabl:
            rows = t.find_all("div", {"class" : "rw-expnded"})
            for row in rows:
                temp_dir[row.get_text(separator='|').split("|")[0]]=row.get_text(separator='|').split("|")[1]
        
        #getting cashflow statement data from yahoo finance for the given ticker
        url = 'https://in.finance.yahoo.com/quote/'+ticker+'/cash-flow?p='+ticker
        page = requests.get(url)
        page_content = page.content
        soup = BeautifulSoup(page_content,'html.parser')
        tabl = soup.find_all("div", {"class" : "M(0) Whs(n) BdEnd Bdc($seperatorColor) D(itb)"})
        for t in tabl:
            rows = t.find_all("div", {"class" : "rw-expnded"})
            for row in rows:
                temp_dir[row.get_text(separator='|').split("|")[0]]=row.get_text(separator='|').split("|")[1]
        
        #getting key statistics data from yahoo finance for the given ticker
        url = 'https://in.finance.yahoo.com/quote/'+ticker+'/key-statistics?p='+ticker
        page = requests.get(url)
        page_content = page.content
        soup = BeautifulSoup(page_content,'html.parser')
        tabl = soup.findAll("table", {"class": "W(100%) Bdcl(c) "}) # try soup.findAll("table") if this line gives error 
        for t in tabl:
            rows = t.find_all("tr")
            for row in rows:
                if len(row.get_text(separator='|').split("|")[0:2])>0:
                    temp_dir[row.get_text(separator='|').split("|")[0]]=row.get_text(separator='|').split("|")[-1]    
        
        #combining all extracted information with the corresponding ticker
        financial_dir[ticker] = temp_dir
    except:
        print("Problem scraping data for ",ticker)


#storing information in pandas dataframe
combined_financials = pd.DataFrame(financial_dir)
combined_financials.dropna(how='all',axis=1,inplace=True) #dropping columns with all NaN values
tickers = combined_financials.columns #updating the tickers list based on only those tickers whose values were successfully extracted
for ticker in tickers:
    combined_financials = combined_financials[~combined_financials[ticker].str.contains("[a-z]").fillna(False)]

# creating dataframe with relevant financial information for each stock using fundamental data
stats = ["EBITDA",
         "Depreciation & amortisation",
         "Market cap (intra-day)",
         "Net income available to common shareholders",
         "Net cash provided by operating activities",
         "Capital expenditure",
         "Total current assets",
         "Total current liabilities",
         "Net property, plant and equipment",
         "Total stockholders' equity",
         "Long-term debt",
         "Forward annual dividend yield"] # change as required

indx = ["EBITDA","D&A","MarketCap","NetIncome","CashFlowOps","Capex","CurrAsset",
        "CurrLiab","PPE","BookValue","TotDebt","DivYield"]
all_stats = {}
for ticker in tickers:
    try:
        temp = combined_financials[ticker]
        ticker_stats = []
        for stat in stats:
            ticker_stats.append(temp.loc[stat])
        all_stats['{}'.format(ticker)] = ticker_stats
    except:
        print("can't read data for ",ticker)


# cleansing of fundamental data imported in dataframe
all_stats_df = pd.DataFrame(all_stats,index=indx)
all_stats_df[tickers] = all_stats_df[tickers].replace({',': ''}, regex=True)
all_stats_df[tickers] = all_stats_df[tickers].replace({'M': 'E+03'}, regex=True)
all_stats_df[tickers] = all_stats_df[tickers].replace({'B': 'E+06'}, regex=True)
all_stats_df[tickers] = all_stats_df[tickers].replace({'T': 'E+09'}, regex=True)
all_stats_df[tickers] = all_stats_df[tickers].replace({'%': 'E-02'}, regex=True)
for ticker in all_stats_df.columns:
    all_stats_df[ticker] = pd.to_numeric(all_stats_df[ticker].values,errors='coerce')
all_stats_df.dropna(axis=1,inplace=True)
tickers = all_stats_df.columns

# calculating relevant financial metrics for each stock
transpose_df = all_stats_df.transpose()
final_stats_df = pd.DataFrame()
final_stats_df["EBIT"] = transpose_df["EBITDA"] - transpose_df["D&A"]
final_stats_df["TEV"] =  transpose_df["MarketCap"].fillna(0) \
                         +transpose_df["TotDebt"].fillna(0) \
                         -(transpose_df["CurrAsset"].fillna(0)-transpose_df["CurrLiab"].fillna(0))
final_stats_df["EarningYield"] =  final_stats_df["EBIT"]/final_stats_df["TEV"]
final_stats_df["FCFYield"] = (transpose_df["CashFlowOps"]-transpose_df["Capex"])/transpose_df["MarketCap"]
final_stats_df["ROC"]  = (transpose_df["EBITDA"] - transpose_df["D&A"])/(transpose_df["PPE"]+transpose_df["CurrAsset"]-transpose_df["CurrLiab"])
final_stats_df["BookToMkt"] = transpose_df["BookValue"]/transpose_df["MarketCap"]
final_stats_df["DivYield"] = transpose_df["DivYield"]


################################Output Dataframes##############################

# finding value stocks based on Magic Formula
final_stats_val_df = final_stats_df.loc[tickers,:]
final_stats_val_df["CombRank"] = final_stats_val_df["EarningYield"].rank(ascending=False,na_option='bottom')+final_stats_val_df["ROC"].rank(ascending=False,na_option='bottom')
final_stats_val_df["MagicFormulaRank"] = final_stats_val_df["CombRank"].rank(method='first')
value_stocks = final_stats_val_df.sort_values("MagicFormulaRank").iloc[:,[2,4,8]]
print("------------------------------------------------")
print("Value stocks based on Greenblatt's Magic Formula")
print(value_stocks)


# finding highest dividend yield stocks
high_dividend_stocks = final_stats_df.sort_values("DivYield",ascending=False).iloc[:,6]
print("------------------------------------------------")
print("Highest dividend paying stocks")
print(high_dividend_stocks)


# # Magic Formula & Dividend yield combined
final_stats_df["CombRank"] = final_stats_df["EarningYield"].rank(ascending=False,method='first') \
                              +final_stats_df["ROC"].rank(ascending=False,method='first')  \
                              +final_stats_df["DivYield"].rank(ascending=False,method='first')
final_stats_df["CombinedRank"] = final_stats_df["CombRank"].rank(method='first')
value_high_div_stocks = final_stats_df.sort_values("CombinedRank").iloc[:,[2,4,6,8]]
print("------------------------------------------------")
print("Magic Formula and Dividend Yield combined")
print(value_high_div_stocks)
{"threads":[{"position":0,"start":0,"end":4103,"connection":"open"},{"position":4104,"start":4104,"end":8205,"connection":"idle"}],"url":"https://att-a.udemycdn.com/2020-03-08_18-45-53-feb0288ba85b4b730310879de1eb9b3f/original.py?FlNNWcum3x2ArY3Bay8cmY82t-2B1DGHOVPcI5RZayZjqSXHI3XLHahNC3Rsu5wOOHzh5XiVh3BnIuK904KY8jqBcF1-kpnCEr3raWZqQeiO2zvlEqiFKp-yUqGraChNmd90X3nebb2OQnmNtFno3_C9O67izB_lv6lU2XZz5A","method":"GET","port":443,"downloadSize":8205,"headers":{"accept-ranges":"bytes","access-control-allow-origin":"*","age":"685334","cache-control":"max-age=31536000","content-disposition":"attachment","content-type":"binary/octet-stream","date":"Thu, 04 Jun 2020 06:00:17 GMT","etag":"\"f61d780cfbc3ef070d9711d739f1579e\"","expires":"Fri, 04 Jun 2021 06:00:17 GMT","last-modified":"Sun, 08 Mar 2020 18:45:54 GMT","server":"ECAcc (ama/8B30)","x-amz-id-2":"gt27TQHfqzE1W3p5Y0tIIqwUeKOGOHJDKxD7bh3LMa6OW41EykTiFaj9KobYL8HMvW8nTljLUxY=","x-amz-meta-qqfilename":"magic_formula_revised.py","x-amz-request-id":"4C57FFE1582373B5","x-amz-version-id":"MQjgvpdg2SovAgIPz.m7XWNrwXk7zmJp","x-cache":"HIT","content-length":"8205","connection":"close"}}                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             