from dateutil.relativedelta import relativedelta
import pandas as pd
from statistics import stdev, mean, variance
import json
from math import sqrt


def port_and(asset_series_dict, quotes):
    #print "port and", asset_series_dict
    i = 0
    df = pd.DataFrame()
    for asset in asset_series_dict:
        asset_series_dict[asset] = asset_series_dict[asset][["date", "price"]]
        asset_series_dict[asset].columns = ["date", asset]
        asset_series_dict[asset][asset] = asset_series_dict[asset][asset].apply(lambda x: x*quotes[asset])
        #print i, asset_series_dict[asset]
        if i == 0:
            df = asset_series_dict[asset]
            df = df.set_index('date')
        else:
            df = df.join(asset_series_dict[asset].set_index('date'))
        #print df
        i += 1
    df["price"] = df.sum(axis=1)
    df.reset_index(level=0, inplace=True)
    return df[["date", "price"]]


def portfolio_value(portfolio_comp, prices):
    value = 0
    for p in portfolio_comp:
        pri = prices.filter(asset_id=p.asset.codec).first()
        value += pri.price*p.quote
    return value


def portfolio_composition(portfolio_comp, prices):
    weights = dict()
    for p in portfolio_comp:
        pri = prices.filter(asset__codec=p.asset.codec).first()
        weights[p.asset.codec] = pri.price * p.quote / portfolio_value(portfolio_comp, prices)
    return weights


def absolute_return(start_price, end_price):
    return end_price/start_price - 1


def annualized_return(start_price, end_price, time):
    print "an_r", time, (end_price / start_price) ** (1 / time) - 1
    return (end_price / start_price)**(1/time) - 1


def difference_date_years(date_start, date_end):
    return (date_end - date_start).days / 365.25


def difference_date(date, time):
    return date - relativedelta(years=time)


def risk_corr(asset_series_dict):
    print asset_series_dict
    rend_dict = dict()
    risks = dict()
    for asset in asset_series_dict:
        asset_df = asset_series_dict[asset]
        start_date = asset_df.iloc[0]["date"]
        end_date = asset_df.iloc[len(asset_df) - 1]["date"]
        end_date += relativedelta(months=1)

        date = start_date
        month_rend = []
        while (date.month != end_date.month) or (date.year != end_date.year):
            z = asset_df[(pd.to_datetime(asset_df["date"]).dt.year == date.year) &
                         (pd.to_datetime(asset_df["date"]).dt.month == date.month)]
            y = z["price"]
            rend = (y.iloc[len(y) - 1] / y.iloc[0]) - 1
            month_rend.append(rend)
            date += relativedelta(months=+1)
        risk = stdev(month_rend) * sqrt(12)
        risks[asset] = risk
        rend_dict[asset] = month_rend

    rend_df = pd.DataFrame.from_dict(rend_dict)
    corr = rend_df.corr()
    return risks, corr


def risk_asset(asset_df):
    print "asset df", asset_df
    start_date = asset_df.iloc[0]["date"]
    end_date = asset_df.iloc[len(asset_df)-1]["date"]
    end_date += relativedelta(months=1)

    date = start_date
    month_rend = []
    while (date.month != end_date.month) or (date.year != end_date.year):
        z = asset_df[(pd.to_datetime(asset_df["date"]).dt.year == date.year) &
                     (pd.to_datetime(asset_df["date"]).dt.month == date.month)]
        y = z["price"]
        print y.iloc[len(y) - 1], y.iloc[0]
        rend = (y.iloc[len(y) - 1] / y.iloc[0]) - 1
        month_rend.append(rend)
        date += relativedelta(months=+1)
    print "Month rend", month_rend
    risk = stdev(month_rend) * sqrt(12)

    return risk


def portfolio_risk(risks, corr, weights):
    y1 = 0
    for asset in risks:
        y1 += weights[asset] ** 2 * risks[asset] ** 2

    y2 = 0
    for asset in risks:
        for asset1 in risks:
            if asset != asset1:
                y2 += weights[asset] * weights[asset] * risks[asset] * risks[asset1] * corr[asset][asset1]
    return sqrt(y1 + y2)


def return_assets(asset_series_dict, start_date, end_date):
    #print asset_series_dict
    time = difference_date_years(start_date, end_date)
    ab_returns = dict()
    an_returns = dict()
    for asset in asset_series_dict:
        asset_f = asset_series_dict[asset]
        print asset_f.iloc[0]["price"], asset_f.iloc[len(asset_f)-1]["price"]
        ab_returns[asset] = absolute_return(asset_f.iloc[0]["price"], asset_f.iloc[len(asset_f)-1]["price"])
        an_returns[asset] = annualized_return(asset_f.iloc[0]["price"], asset_f.iloc[len(asset_f)-1]["price"], time)
    return an_returns, ab_returns


def portfolio_return(weights, an_returns, ab_returns):
    annualized_r = 0
    absolute_r = 0
    for asset in weights:
        annualized_r += weights[asset]*an_returns[asset]
        absolute_r += weights[asset]*ab_returns[asset]
    return annualized_r, absolute_r


def portfolio_statistics(asset_series_dict, start_date, end_date, weights):
    risks, corr = risk_corr(asset_series_dict, start_date, end_date)
    p_risk = portfolio_risk(risks, corr, weights)
    an_returns, ab_returns = return_assets(asset_series_dict, start_date, end_date)
    annualized_r, absolute_r = portfolio_return(weights, an_returns, ab_returns)

    p_statistics = dict()
    p_statistics["absolute_return"] = absolute_r
    p_statistics["annualized_return"] = annualized_r
    p_statistics["portfolio_risk"] = p_risk
    #p_statistics["correlation_asset"] = corr

    asset_statistics = dict()
    for asset in weights:
        asset_statistics[asset] = {
            "weight": weights[asset],
            "absolute_return": ab_returns[asset],
            "annualized_return": an_returns[asset],
            "risk": risks[asset],
        }
    return p_statistics, asset_statistics


def objectives_query_set_minus_savings_to_dict(objectives, yearly_savings):
    objectives_dict = dict()
    time_horizon = 0
    savings = 0
    for objective in objectives:
        objectives_dict[objective.id] = {
            "finality": objective.finality,
            "value": objective.finalValue,
            "time_horizon": objective.time_horizon,
            "priority": objective.priority
        }
        saving_par = (objective.time_horizon - time_horizon) * yearly_savings + savings
        val = objective.finalValue - saving_par
        if val >= 0:
            objectives_dict[objective.id]["value_minus_savings"] = objective.finalValue - saving_par
            objectives_dict[objective.id]["savings_required"] = saving_par
            savings = 0
        else:
            objectives_dict[objective.id]["value_minus_savings"] = 0
            objectives_dict[objective.id]["savings_required"] = objective.finalValue
            savings = saving_par - objective.finalValue
        time_horizon = objective.time_horizon
    return objectives_dict
