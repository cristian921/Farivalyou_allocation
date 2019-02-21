from math import sqrt


def risk_portfolio(weights, risks, corr):
    y1 = 0
    for asset in risks:
        y1 += risks[asset] ** 2 * weights[asset] ** 2
    y2 = 0
    for asset in risks:
        for asset1 in risks:
            y2 += risks[asset] * risks[asset1] * weights[asset] * weights[asset1] * corr[asset][asset1]
    return sqrt(y1 + y2)


def get_weights(quotes, prices):
    weights = dict()
    value = 0
    i = 0
    for asset in prices:
        value += quotes[i] * prices[asset]
        i += 1
    i = 0
    for asset in prices:
        weights[asset] = quotes[i] * prices[asset] / value
        i += 1
    return weights


def return_portfolio(returns, weights):
    return_p = 0
    for asset in returns:
        return_p += returns[asset] * weights[asset]
    return return_p


def portfolio_value(prices, quotes):
    value = 0
    i = 0
    for asset in prices:
        value += prices[asset] * quotes[i]
        i += 1
    return value
