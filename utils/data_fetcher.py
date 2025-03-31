import yfinance as yf
import pandas as pd
import fundamentus as fd

def fetch_stock_data(tickers):
    tickers = [i+'.SA' for i in tickers]
    data = yf.download(tickers)['Close'].dropna()
    data.columns = data.columns.str.replace(r'\.SA$', '', regex=True)
    
    return data

def fetch_stock_results(tickers):
    df_p = pd.DataFrame();
    for ticker in tickers:
        df_p = pd.concat([df_p,fd.get_papel(ticker)])
    
    df = fd.get_resultado()

    df_p = pd.concat([df_p[['Empresa','Setor','Div_Br_Patrim']],df[['dy','pl','pvp']]],axis = 1).dropna()
    df_p['dy'] = df_p.dy*100
    df_p['Div_Br_Patrim'] = df_p.Div_Br_Patrim.replace('-',None).astype(float) / 100

    return df_p