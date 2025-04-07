import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objs as go
from datetime import datetime
from utils.data_fetcher import fetch_stock_data, fetch_stock_results
from bcb import sgs
from arch import arch_model

# Carrega os dados dos tickers a partir de um CSV com informações de nome e setor

@st.cache_data
def load_ticker_data():
    return pd.read_csv('sectors.csv')

# Simula carteiras aleatórias usando Monte Carlo para encontrar composição ótima com base no índice de Sharpe

@st.cache_data
def monte_carlo_portfolios(returns, n_simulations=3000):
    results = []
    num_assets = len(returns.columns) # Número de ativos selecionados

    for _ in range(n_simulations):
        weights = np.random.random(num_assets) # Gera pesos aleatórios
        weights /= np.sum(weights)  # Normaliza para somarem 1
        ret = np.sum(returns.mean() * weights) * 252 # Retorno anualizado
        vol = np.sqrt(np.dot(weights.T, np.dot(returns.cov()*252, weights))) # Volatilidade anualizada
        sharpe = ret / vol # Índice de Sharpe
        results.append((weights, ret, vol, sharpe))
          
    # Retorna as carteiras ordenadas pelo maior índice de Sharpe

    results_df = pd.DataFrame(results, columns=['weights', 'return', 'volatility', 'sharpe'])
    return results_df.sort_values(by='sharpe', ascending=False)

# Carrega dados da tabela de tickers
tickers_df = load_ticker_data()
tickers_df['display'] = tickers_df['tick'] + ' - ' + tickers_df['stock_name']

st.title('📈 Otimização de Carteira com Monte Carlo')

# Inicialização dos estados da aplicação
if 'num_stocks' not in st.session_state:
    st.session_state['num_stocks'] = 2
if 'carteira_calculada' not in st.session_state:
    st.session_state['carteira_calculada'] = False
if 'periodo_atual' not in st.session_state:
    st.session_state['periodo_atual'] = 'Completo'
if 'forcar_recalculo' not in st.session_state:
    st.session_state['forcar_recalculo'] = False

# Botões para adicionar ou remover ações
col_sub, col_add, _ = st.columns([0.1, 0.1, 0.8])

with col_sub:
    if st.button('➖') and st.session_state['num_stocks'] > 2:
        st.session_state['num_stocks'] -= 1
        st.session_state['carteira_calculada'] = False
with col_add:
    if st.button('➕') and st.session_state['num_stocks'] < 12:
        st.session_state['num_stocks'] += 1
        st.session_state['carteira_calculada'] = False

# Mostra o número atual de ações selecionadas
num_stocks = st.session_state['num_stocks']
st.write(f'Número de ações selecionadas: {num_stocks}')

# Coleta as ações escolhidas pelo usuário
selected_stocks = []
selected_sectors = []
selected_company = {}
invalid_selection = False

# Gera os seletores de ações dinamicamente
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

# Verifica se houve mudança nas ações selecionadas para forçar novo cálculo
previous_tickers = set(st.session_state.get('selected_stocks_saved', []))
current_tickers = set(selected_stocks)
if previous_tickers != current_tickers:
    st.session_state['carteira_calculada'] = False

# Alerta se houver seleções inválidas
if invalid_selection:
    st.warning("⚠️ Por favor, selecione todas as ações antes de prosseguir.")

# Remove duplicações e mantém setores
selected_stocks = np.unique(selected_stocks)
selected_sectors = selected_sectors

# Número de simulações do modelo de Monte Carlo
num_simulations = st.number_input('Número de simulações Monte Carlo:', min_value=500, max_value=10000, value=3000, step=500, help='Aumentar o número de simulações pode aumentar o tempo de cálculo.')

# Define se o cálculo deve ser executado
recalcular = False

# Botão principal que dispara o cálculo da carteira
if st.button('Calcular Carteira Otimizada'):
    recalcular = True
elif st.session_state.get('carteira_calculada', False):
    old = set(st.session_state.get('selected_stocks_saved', []))
    new = set(selected_stocks)
    if old != new:
        recalcular = True


# Bloco principal de cálculo e armazenamento dos dados otimizados
if recalcular:
    data = fetch_stock_data(selected_stocks)  # Coleta dados históricos das ações
    # Separa os dados do índice Ibovespa para comparação visual
    ibovespa_returns = data['^BVSP'].pct_change().dropna()
    data = data.drop(columns=['^BVSP'])  # Remove Ibovespa dos cálculos da carteira
    # Calcula os retornos percentuais diários
    returns = data.pct_change().dropna()
    # Armazena os dados brutos para uso posterior (ex: análises por período)
    st.session_state['data'] = data
    st.session_state['bvsp'] = ibovespa_returns
    # Executa simulação de Monte Carlo com os retornos obtidos
    monte_carlo_results = monte_carlo_portfolios(returns, n_simulations=num_simulations)
    best_weights = monte_carlo_results.iloc[0]['weights']  # Seleciona a carteira com maior Sharpe

    # Salva os resultados em cache para uso posterior
    st.session_state['returns'] = returns
    st.session_state['weights'] = best_weights
    st.session_state['selected_stocks_saved'] = selected_stocks
    st.session_state['carteira_calculada'] = True
    st.session_state['monte_carlo_results'] = monte_carlo_results
    st.session_state['periodo_atual'] = 'Completo'
    st.session_state['forcar_recalculo'] = True

    st.success("Carteira otimizada carregada!")

# A partir deste ponto, o restante do cálculo e visualização será executado
# Bloco de visualização e ajuste da carteira calculada
if st.session_state.get('carteira_calculada', False):
    # Recupera os dados brutos salvos
    data = st.session_state['data']
    
    ibovespa_returns = st.session_state['bvsp']

    # Recalcula os retornos com base nos dados armazenados
    returns = data.pct_change().dropna()

    # Interface para seleção do período de análise
    period_choice = st.radio(
        'Selecione o período para análise:',
        ['YTD', '1 Ano', '5 Anos','Completo'],
        index=1,
        horizontal=True
    )

    # Impede que o app pare caso estejamos apenas interagindo com o slider
    executando_slider = f'return_slider_{period_choice}' in st.session_state
    if not st.session_state.get('forcar_recalculo', False) and period_choice == st.session_state.get('periodo_atual') and not executando_slider:
        st.stop()

    st.session_state['periodo_atual'] = period_choice
    st.session_state['forcar_recalculo'] = False

    # Define a data de início com base na seleção
    today = datetime.today()
    if period_choice == 'YTD':
        start_date = datetime(today.year, 1, 1)
    elif period_choice == '1 Ano':
        start_date = today - pd.DateOffset(years=1)
    elif period_choice == '5 Anos':
        start_date = today - pd.DateOffset(years=5)
    else:
        start_date = returns.index[0]

    # Gera novo conjunto de retornos com base no período filtrado
    # Sempre recalcula period_returns com base nas ações mais recentes
    key_period = f'monte_carlo_{period_choice}'

    period_returns = returns[returns.index >= start_date].dropna(axis=1, how='any')
    monte_carlo_results_period = monte_carlo_portfolios(period_returns, n_simulations=num_simulations)
    st.session_state['forcar_recalculo'] = False

    # Prepara os dados para o slider de retorno
    monte_carlo_results_period['return_pct'] = np.round(monte_carlo_results_period['return'] * 100, 2)
    returns_slider = np.round(monte_carlo_results_period['return_pct'].unique(), 2)
    returns_slider.sort()
    optimal_return_period = np.round(monte_carlo_results_period.iloc[0]['return_pct'], 2)
    step_slider = max(np.round((returns_slider.max() - returns_slider.min()) / len(returns_slider), 2), 0.01)

    # Slider interativo que permite o usuário escolher o retorno da carteira
    return_selected_percent = st.slider(
        'Selecione o retorno anual (%)',
        min_value=float(returns_slider.min()),
        max_value=float(returns_slider.max()),
        value=float(optimal_return_period),
        step=float(step_slider),
        key=f'return_slider_{period_choice}'
    )

    # Recupera os pesos da carteira mais próxima do retorno selecionado
    closest_idx = (monte_carlo_results_period['return_pct'] - return_selected_percent).abs().idxmin()
    closest_return_row = monte_carlo_results_period.loc[closest_idx]
    selected_weights = closest_return_row['weights']

    # Calcula a rentabilidade acumulada da carteira ao longo do tempo
    portfolio_cumulative = ((period_returns @ selected_weights + 1).cumprod() - 1) * 100

    # Coleta dados da SELIC e da Inflação (IPCA) para comparação
    selic = sgs.get({'selic':4189}, start = str(start_date.date()))
    selic_final = selic.selic.iloc[-1] / 100
    selic = (selic.dropna()/12).cumsum()
    inflacao = sgs.get({'ipca':13522}, start = str(start_date.date()))
    inflacao = (inflacao.dropna()/12).cumsum()

    ibovespa_returns = ibovespa_returns.loc[str(start_date.date()):]

    # Geração do gráfico comparativo da rentabilidade da carteira, SELIC e inflação
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=portfolio_cumulative.index, y=portfolio_cumulative, name='Carteira Otimizada'))
    fig.add_trace(go.Scatter(x=selic.index, y=selic.selic, name='SELIC', opacity=0.6))
    fig.add_trace(go.Scatter(x=inflacao.index, y=inflacao.ipca, name='Inflação', opacity=0.6))
    fig.add_trace(go.Scatter(x=ibovespa_returns.index, y=((ibovespa_returns + 1).cumprod() - 1) * 100, name='Ibovespa', opacity=0.6, line=dict(color='gray')))

    fig.update_layout(
        title='Rentabilidade Acumulada da Carteira Otimizada (%)',
        xaxis_title='Data',
        yaxis_title='Rentabilidade Acumulada (%)',
        yaxis_tickformat=".1f"
    )    
    st.plotly_chart(fig)

    # Exibe os principais indicadores da carteira (com base na seleção do usuário)
    annual_ret = closest_return_row['return']
    annual_vol = closest_return_row['volatility']
    st.subheader('Retorno e Risco da Carteira')
    st.write(f'Retorno anual: {annual_ret:.2%}')
    st.write(f'Volatilidade anual: {annual_vol:.2%}')

    # Busca indicadores fundamentalistas das ações selecionadas
    stock_results_df = fetch_stock_results(period_returns.columns.tolist())
    stock_results_df = stock_results_df.set_index('Empresa')

    # Calcula dividend yield ponderado pela proporção das ações na carteira
    dy_series = stock_results_df.loc[[selected_company[c] for c in period_returns.columns], 'dy'].astype(float).values
    dy_ponderado = np.sum(selected_weights * dy_series) / len(dy_series)
    st.write(f'Dividend Yield médio da carteira: {np.round(dy_ponderado,2)}%')


    # Estima volatilidade condicional usando o modelo GJR-GARCH(1,1,1)
    portfolio_returns = period_returns @ selected_weights
    am = arch_model(portfolio_returns * 100, vol='GARCH', p=1, o=1, q=1, dist='normal')
    res = am.fit(disp='off')
    conditional_volatility = res.conditional_volatility / 100

    # Gráfico da volatilidade condicional
    fig_vol = go.Figure()
    fig_vol.add_trace(go.Scatter(
        x=portfolio_returns.index, 
        y=conditional_volatility, 
        name='Volatilidade (GJR-GARCH)',
        line=dict(color='orange')
    ))
    fig_vol.update_layout(yaxis_title="Volatilidade diária")

    st.markdown("### Volatilidade Condicional da Carteira (GJR-GARCH)")
    st.info("ℹ️ A volatilidade condicional é calculada usando o modelo GJR-GARCH para capturar mudanças na volatilidade ao longo do tempo, especialmente durante períodos de maior instabilidade no mercado. Valores mais altos indicam períodos de maior risco, enquanto valores menores sugerem períodos de maior estabilidade.")
    st.plotly_chart(fig_vol)

    # Classifica P/VP com emojis de "preço justo"
    pvp_valores = stock_results_df.loc[[selected_company[c] for c in period_returns.columns], 'pvp'].astype(float).values
    pvp_emojis = []
    for v in pvp_valores:
        if v < 0:
            pvp_emojis.append('💸')
        elif v < 1:
            pvp_emojis.append('💲')
        elif v < 2:
            pvp_emojis.append('💲💲')
        else:
            pvp_emojis.append('💲💲💲')
            
    emojis = []

    # Classifica Dívida Bruta / Patrimônio com emojis visuais
    divida_valores = stock_results_df.loc[[selected_company[c] for c in period_returns.columns], 'Div_Br_Patrim'].astype(float).values
    for v in divida_valores:
        if pd.isna(v):
            emojis.append('⚪')
        elif v < 0:
            emojis.append('🔴❗')
        elif v < 0.5:
            emojis.append('🟢')
        elif v < 1:
            emojis.append('🟡')
        else:
            emojis.append('🔴')

    # Classifica P/L com base na comparação com o tempo que a SELIC levaria para retornar o investimento
    pl_valores = stock_results_df.loc[[selected_company[c] for c in period_returns.columns], 'pl'].astype(float).values
    selic_anos = 1 / selic_final if selic_final > 0 else np.inf
    pl_emojis = ['✅' if v < selic_anos else '❌' for v in pl_valores]

    # Monta DataFrame final com composição da carteira e indicadores fundamentalistas
    comp_df = pd.DataFrame({
        'Ticker': period_returns.columns,
        'Empresa': [selected_company[c] for c in period_returns.columns],
        'Peso (%)': np.round(selected_weights * 100, 2),
        'Dividendos (%)': stock_results_df.loc[[selected_company[c] for c in period_returns.columns], 'dy'].astype(float).values,
        'Retorna rápido?': pl_emojis,
        'Está barato?': pvp_emojis,
        'Deve muito?': emojis
    })

    # Exibe a tabela com os dados de composição
    st.subheader('Composição Percentual da Carteira')
    st.dataframe(comp_df, hide_index=True)

    # Exibe a legenda com explicação dos emojis usados
    st.caption("Legenda:")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.info("""🔹 **Retorna rápido ?**:  
Usa-se o indicador P/L que mede quantos anos a ação leva para retornar seu investimento com base nos lucros. Comparado à SELIC.
                
   ✅ Em menos tempo do que da SELIC  
        ❌ Leva mais tempo do que SELIC """)
    with col2:
        st.info("""🔹 **Está barato?**:                
Através do indicador P/VP, avalia-se o preço atual do ativo em relação ao valor patrimonial por ação.
        
💲 No precinho!  
        💲💲 Barato mas nem tanto 
        💲💲💲 Tá caro!  
        💸 Fuja! 
""")
    with col3:
        st.info("""
🔹 **Deve muito?**:   
Dívida Bruta/Patrimônio, onde medimos o nível de endividamento em relação ao patrimônio da empresa.
        
🟢 Dívidas sob-controle  
        🟡 Deve menos do que possui... por enquanto...  
        🔴 Dívida maior do que o patrimônio  
        🔴❗ Patrimônio negativado (atenção)  
        ⚪ Informação indisponível  
""")

    # Prepara os dados e gera gráfico da composição da carteira por setor
    setores = []
    for t in selected_stocks:
        setor_match = tickers_df[tickers_df['tick'] == t]['sector']
        setores.append(setor_match.values[0] if not setor_match.empty else 'Setor não encontrado')

    sector_df = pd.DataFrame({'Setor': setores, 'Peso': selected_weights})
    sector_df = sector_df.groupby('Setor').sum().reset_index()

    # Geração do gráfico circular ao final da página
    fig_sector = go.Figure(go.Pie(labels=sector_df['Setor'], values=sector_df['Peso'], hole=.4))
    fig_sector.update_layout(title='Composição da Carteira por Setor')
    st.plotly_chart(fig_sector)