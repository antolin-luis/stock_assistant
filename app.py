import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objs as go
from datetime import datetime
from utils.data_fetcher import fetch_stock_data,fetch_sectors
from bcb import sgs

@st.cache_data
def load_ticker_data():
    return pd.read_csv('sectors.csv')

@st.cache_data
def monte_carlo_portfolios(returns, n_simulations=3000):
    results = []
    num_assets = len(returns.columns)

    for _ in range(n_simulations):
        weights = np.random.random(num_assets)
        weights /= np.sum(weights)
        ret = np.sum(returns.mean() * weights) * 252
        vol = np.sqrt(np.dot(weights.T, np.dot(returns.cov()*252, weights)))
        sharpe = ret / vol
        results.append((weights, ret, vol, sharpe))

    results_df = pd.DataFrame(results, columns=['weights', 'return', 'volatility', 'sharpe'])
    return results_df.sort_values(by='sharpe', ascending=False)

tickers_df = load_ticker_data()
tickers_df['display'] = tickers_df['tick'] + ' - ' + tickers_df['stock_name']

st.title('📈 Otimização de Carteira com Monte Carlo')

# Inicializa contador de ações
if 'num_stocks' not in st.session_state:
    st.session_state['num_stocks'] = 2

# Botões para aumentar ou diminuir o número de ações mais próximos
col_sub, col_add, _ = st.columns([0.1, 0.1, 0.8])

with col_sub:
    if st.button('➖') and st.session_state['num_stocks'] > 2:
        st.session_state['num_stocks'] -= 1

with col_add:
    if st.button('➕') and st.session_state['num_stocks'] < 10:
        st.session_state['num_stocks'] += 1


num_stocks = st.session_state['num_stocks']
st.write(f'Número de ações selecionadas: {num_stocks}')

# Seletores das ações, 4 por linha
selected_stocks = []
selected_sectors = []
selected_company = {}
invalid_selection = False  

for i in range(num_stocks):
    if i % 4 == 0:
        cols = st.columns(4)
    selected = cols[i % 4].selectbox(
        f'Ação {i+1}', 
        options=["Selecione uma ação..."] + tickers_df['display'].tolist(), 
        key=f'stock_{i}'
    )

    if selected == "Selecione uma ação...":
        invalid_selection = True
    else:
        ticker = selected.split(' - ')[0]
        sector = tickers_df[tickers_df['tick'] == ticker]['sector'].values[0]
        selected_stocks.append(ticker)
        selected_sectors.append(sector)
        selected_company[ticker] = tickers_df[tickers_df['tick'] == ticker]['stock_name'].values[0]

# Apenas exibe aviso se o usuário ainda não selecionou todas as ações
if invalid_selection:
    st.warning("⚠️ Por favor, selecione todas as ações antes de prosseguir.")

selected_stocks = np.unique(selected_stocks)
selected_sectors = np.unique(selected_sectors)

num_simulations = st.number_input('Número de simulações Monte Carlo:', min_value=500, max_value=10000, value=3000, step=500, help='(i) Aumentar o número de simulações pode aumentar o tempo de cálculo.')

# Esta variável controla se a carteira já foi calculada pelo usuário explicitamente
if 'carteira_calculada' not in st.session_state:
    st.session_state['carteira_calculada'] = False

if st.button('Calcular Carteira Otimizada'):
    data = fetch_stock_data(selected_stocks)
    returns = data.pct_change().dropna()

    monte_carlo_results = monte_carlo_portfolios(returns, n_simulations=num_simulations)
    best_weights = monte_carlo_results.iloc[0]['weights']

    st.session_state['returns'] = returns
    st.session_state['weights'] = best_weights
    st.session_state['selected_stocks_saved'] = selected_stocks  # novo!
    st.session_state['carteira_calculada'] = True
    st.session_state['monte_carlo_results'] = monte_carlo_results
    st.success("Carteira otimizada carregada!")

# Executa os cálculos SOMENTE se o usuário já clicou explicitamente no botão
if 'monte_carlo_results' in st.session_state:
    returns = st.session_state['returns']

    period_choice = st.radio(
        'Selecione o período para análise:',
        ['YTD', '1 Ano', '5 Anos','Completo'],
        index=1,
        horizontal=True
    )

    today = datetime.today()
    if period_choice == 'YTD':
        start_date = datetime(today.year, 1, 1)
    elif period_choice == '1 Ano':
        start_date = today - pd.DateOffset(years=1)
    elif period_choice == '5 Anos':
        start_date = today - pd.DateOffset(years=5)
    else:
        start_date = returns.index[0]

    key_period = f'monte_carlo_{period_choice}'
    if key_period not in st.session_state:
        period_returns = returns[returns.index >= start_date].dropna(axis=1, how='any')
        monte_carlo_results_period = monte_carlo_portfolios(period_returns, n_simulations=num_simulations)
        st.session_state[key_period] = {
            'returns': period_returns,
            'monte_carlo': monte_carlo_results_period
        }

    period_data = st.session_state[key_period]
    period_returns = period_data['returns']
    
    # Recupera o dataframe original do monte carlo
    monte_carlo_results_period = period_data['monte_carlo'].copy()

    # Transforma a coluna return em percentual APENAS NA CÓPIA
    monte_carlo_results_period['return_pct'] = monte_carlo_results_period['return'] * 100
    monte_carlo_results_period['return_pct'] = np.round(monte_carlo_results_period['return_pct'] ,2)

    # Slider usa a coluna em percentual
    returns_slider = np.round(monte_carlo_results_period['return_pct'].unique(), 2)
    returns_slider.sort()

    step_slider = max(np.round((returns_slider.max() - returns_slider.min()) / len(returns_slider), 2), 0.01)
    optimal_return_period = np.round(monte_carlo_results_period.iloc[0]['return_pct'], 2)

    return_selected_percent = st.slider(
        'Selecione o retorno anual (%)',
        min_value=float(returns_slider.min()),
        max_value=float(returns_slider.max()),
        value=float(optimal_return_period),
        step=float(step_slider),
        key=f'return_slider_{period_choice}'
    )

    # Agora a busca será feita corretamente usando 'return_pct'
    closest_idx = (monte_carlo_results_period['return_pct'] - return_selected_percent).abs().idxmin()
    closest_return_row = monte_carlo_results_period.loc[closest_idx]

    selected_weights = closest_return_row['weights']

    portfolio_cumulative = ((period_returns @ selected_weights + 1).cumprod() - 1) * 100

    selic = sgs.get({'selic':4189}, start = str(start_date.date()))
    selic = (selic.dropna()/12).cumsum()
    inflacao = sgs.get({'ipca':13522}, start = str(start_date.date()))
    inflacao = (inflacao.dropna()/12).cumsum()

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=portfolio_cumulative.index, y=portfolio_cumulative, name='Carteira Otimizada'))
    fig.add_trace(go.Scatter(x=selic.index, y=selic.selic, name='SELIC', opacity=0.6))
    fig.add_trace(go.Scatter(x=inflacao.index, y=inflacao.ipca, name='Inflação', opacity=0.6))

    fig.update_layout(
        title='Rentabilidade Acumulada da Carteira Otimizada (%)',
        xaxis_title='Data',
        yaxis_title='Rentabilidade Acumulada (%)',
        yaxis_tickformat=".1f"
    )    
    st.plotly_chart(fig)

    # Indicadores perfeitamente alinhados:
    annual_ret = closest_return_row['return']
    annual_vol = closest_return_row['volatility']
    st.subheader('Retorno e Risco da Carteira')
    st.write(f'Retorno anual: {annual_ret:.2%}')
    st.write(f'Volatilidade anual: {annual_vol:.2%}')

    comp_df = pd.DataFrame({
        'Ticker': period_returns.columns,
        'Empresa': [selected_company[c] for c in period_returns.columns],
        'Peso (%)': np.round(selected_weights * 100, 2)
    })
    st.subheader('Composição Percentual da Carteira')
    st.dataframe(comp_df, hide_index=True)

    sector_df = pd.DataFrame({'Setor': selected_sectors, 'Peso': selected_weights})
    sector_df = sector_df.groupby('Setor').sum().reset_index()

    fig_sector = go.Figure(go.Pie(labels=sector_df['Setor'], values=sector_df['Peso'], hole=.4))
    fig_sector.update_layout(title='Composição da Carteira por Setor')
    st.plotly_chart(fig_sector)