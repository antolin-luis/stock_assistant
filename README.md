# 📈 Otimização de Carteira de Investimentos com Monte Carlo

Este projeto consiste em uma aplicação interativa desenvolvida com **Python** e **Streamlit**, com o objetivo de auxiliar investidores no estudo e simulação de carteiras de ações do mercado brasileiro. A aplicação utiliza métodos quantitativos avançados para otimizar carteiras e avaliar seu desempenho histórico.

## 🚨 Aviso Importante

**Este projeto possui caráter exclusivamente educacional e não substitui o auxílio de um profissional autorizado na área de investimentos. Utilize-o como ferramenta complementar ao seu estudo pessoal sobre investimentos.**

---

## 🔍 Metodologia e Funcionamento

Todo o processo de **ETL (Extração, Transformação e Carregamento)** é realizado diretamente no script:

- **Extração**: Os dados são coletados através das APIs do **Banco Central (BCB)** e do **Fundamentus**, garantindo informações atualizadas sobre mercado e indicadores financeiros.
- **Transformação**: Aplicam-se métodos quantitativos avançados como a simulação Monte Carlo e modelos econométricos GJR-GARCH para otimizar e avaliar carteiras.
- **Carregamento**: Os resultados finais e visualizações são carregados e exibidos diretamente no Streamlit, permitindo interação em tempo real com o usuário.

### 1. **Seleção das Ações**

O usuário pode selecionar entre **2 a 10 ações** listadas na bolsa brasileira (B3). As ações são escolhidas por meio de uma interface interativa.

### 2. **Simulação Monte Carlo**

Após a seleção das ações, o aplicativo executa milhares de simulações de carteiras com pesos aleatórios. Cada carteira simulada é avaliada pelo seu retorno esperado anualizado, volatilidade anualizada e índice de Sharpe (relação retorno/risco).

A carteira com o maior índice de Sharpe é apresentada como a carteira otimizada.

### 3. **Avaliação da Volatilidade**

Para quantificar e visualizar a volatilidade histórica da carteira selecionada, o modelo **GJR-GARCH(1,1,1)** é aplicado. Esse modelo captura a volatilidade condicional e o efeito assimétrico das notícias sobre o mercado, oferecendo uma visão mais realista do risco da carteira.

### 4. **Comparação com Indicadores Econômicos**

A aplicação exibe gráficos comparativos da rentabilidade histórica da carteira em relação à:

- Taxa básica de juros (SELIC)
- Inflação acumulada (IPCA)

### 5. **Indicadores Fundamentalistas**

A carteira selecionada é complementada com análises fundamentalistas das ações, incluindo:

- Dividend Yield ponderado
- Indicadores financeiros como Dívida Bruta/Patrimônio, P/L e P/VP
- Emojis visuais intuitivos que classificam a saúde financeira das empresas

---

## 🛠️ Tecnologias Utilizadas

- **Python**
- **Streamlit** (interface interativa)
- **Pandas e NumPy** (manipulação e cálculo de dados)
- **Plotly** (visualizações interativas)
- **arch** (modelos de volatilidade GARCH)
- **scipy** (otimização matemática)

---

## 🚀 Como Utilizar

### Instalação das dependências

```bash
pip install -r requirements.txt
```

### Execução da aplicação

```bash
streamlit run app.py
```

Abra seu navegador e acesse `http://localhost:8501`.

---

## 📝 Estrutura do Projeto

```
📁 utils
  ├── data_fetcher.py   # Coleta dados de mercado e indicadores
  ├── monte_carlo.py    # Simulação de carteiras Monte Carlo
  ├── indicators.py     # Cálculos e classificações dos indicadores
  └── ui_elements.py    # Elementos visuais reutilizáveis

📄 app.py                # Aplicação principal Streamlit
📄 sectors.csv           # Lista de ações e seus setores
📄 requirements.txt      # Dependências do projeto
```

---

## 🤝 Colaborações

Contribuições, sugestões e melhorias são bem-vindas. Sinta-se à vontade para abrir uma issue ou pull request!

---

## 📌 Licença

Este projeto está disponível para uso educacional e pessoal, não comercial.

---

📩 **Dúvidas ou sugestões? Entre em contato!**

