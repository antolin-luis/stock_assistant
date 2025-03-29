import yfinance as yf
import pandas as pd
import fundamentus as fd

def fetch_stock_data(tickers):
    tickers = [i+'.SA' for i in tickers]
    data = yf.download(tickers)['Close'].dropna()
    data.columns = data.columns.str.replace(r'\.SA$', '', regex=True)
    
    return data

def fetch_sectors(tickers):
    df_p = pd.DataFrame();
    for ticker in tickers:
        df_p = pd.concat([df_p,fd.get_papel(ticker)])
    
    df = fd.get_resultado()

    df_p = pd.concat([df_p[['Empresa','Setor','VPA']],df[['dy','pl','pvp']]],axis = 1).dropna()

    return df_p