import numpy as np
from scipy.optimize import minimize

def portfolio_stats(weights, returns_cov):
    portfolio_return = np.sum(returns_cov.mean() * weights) * 252
    portfolio_volatility = np.sqrt(np.dot(weights.T, np.dot(returns_cov.cov()*252, weights)))
    return portfolio_return, portfolio_volatility

def negative_sharpe(weights, returns_cov, risk_free_rate=0.12):
    p_return, p_volatility = portfolio_stats(weights, returns_cov)
    return -(p_return - risk_free_rate) / p_volatility

def optimize_portfolio(returns_cov):
    num_assets = len(returns_cov.columns)
    constraints = ({'type': 'eq', 'fun': lambda x: np.sum(x) - 1})
    bounds = tuple((0, 1) for _ in range(num_assets))
    initial_weights = num_assets * [1. / num_assets,]

    result = minimize(negative_sharpe, initial_weights, args=(returns_cov,), method='SLSQP',
                      bounds=bounds, constraints=constraints)

    return result.x