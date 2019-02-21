# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render, get_object_or_404, render_to_response
from django.http import  HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from .forms import *
from utilities.utility import *
from datetime import datetime as dt
import pandas as pd
from django.template.defaulttags import register
from optimization.optimization import optimize_ob
import holidays
import json


holidays_us = holidays.UnitedStates()
holidays_it = holidays.Italy()

@register.filter
def val(value):
    return round(value, 2)


@register.filter
def percentage(value):
    return round(value*100, 2)


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)


@register.filter
def get_price(queryset, value):
    return queryset.filter(asset_id=value).first().price


today = dt.strptime("2019-01-29", '%Y-%m-%d').date()


@login_required(login_url='/registration/login/')
def add_objective(request):
    form = ObjectiveForm(request.POST or None)
    form.fields["user"].initial = request.user
    if form.is_valid():
        form.save()
        return HttpResponseRedirect('/allocation/')
    return render(request, 'allocation/form_objective.html', {'form': form})


@login_required(login_url='/registration/login/')
def update_objective(request, pk):
    objective = get_object_or_404(Objective, pk=pk)
    form = ObjectiveForm(request.POST or None, instance=objective)
    form.fields["user"].initial = request.user
    if form.is_valid():
        objective.id = pk
        form.save()
        return HttpResponseRedirect('/allocation/')
    return render(request, 'allocation/form_objective.html', {'form': form})


@login_required(login_url='/registration/login/')
def delete_objective(request, pk):
    objective = get_object_or_404(Objective, pk=pk)
    if request.method == 'POST':
        objective.delete()
        return HttpResponseRedirect('/allocation/')
    return render(request, 'allocation/confirm_delete.html', {'object': objective})


@login_required(login_url='/registration/login/')
def add_resources(request):
    form = ResourcesForm(request.POST or None)
    form.fields["user"].initial = request.user
    if form.is_valid():
        form.save()
        return HttpResponseRedirect('/allocation/')
    return render(request, 'allocation/form_resources.html', {'form': form})


@login_required(login_url='/registration/login/')
def update_resources(request, pk):
    resources = get_object_or_404(UserResource, pk=pk)
    form = ResourcesForm(request.POST or None, instance=resources)
    form.fields["user"].initial = request.user
    if form.is_valid():
        form.save()
        return HttpResponseRedirect('/allocation/')
    return render(request, 'allocation/form_resources.html', {'form': form})


@login_required(login_url='/registration/login/')
def delete_resources(request, pk, template_name='books/confirm_delete.html'):
    resources = get_object_or_404(UserResource, pk=pk)
    if request.method == 'POST':
        resources.delete()
        return HttpResponseRedirect('book_list')
    return render(request, template_name, {'object': resources})


@login_required(login_url='/registration/login/')
def add_aggregated_portfolio(request):
    form = AggregatedPortfolioForm(request.POST or None)
    form.fields["user"].initial = request.user
    if form.is_valid():
        form.save()
        return HttpResponseRedirect('/allocation/')
    return render(request, 'allocation/form_aggregated_portfolio.html', {'form': form})


@login_required(login_url='/registration/login/')
def update_aggregated_portfolio(request, pk):
    aggregated_portfolio = get_object_or_404(AggregatedPortfolio, pk=pk)
    form = ObjectiveForm(request.POST or None, instance=aggregated_portfolio)
    form.fields["user"].initial = request.user
    if form.is_valid():
        form.save()
        return HttpResponseRedirect('/allocation/')
    return render(request, 'allocation/form_aggregated_portfolio.html', {'form': form})


@login_required(login_url='/registration/login/')
def delete_aggregated_portfolio(request, pk):
    aggregated_portfolio = get_object_or_404(AggregatedPortfolio, pk=pk)
    if request.method == 'POST':
        aggregated_portfolio.delete()
        return HttpResponseRedirect('/allocation/')
    return render(request, 'allocation/confirm_delete.html', {'object': aggregated_portfolio})


@login_required(login_url='/registration/login/')
def add_asset_portfolio(request, pk):
    aggregated_portfolio = AggregatedPortfolio.objects.filter(pk=pk).first()
    form = PortfolioAssetForm(request.POST or None)
    form.fields["aggregated_portfolio"].initial = aggregated_portfolio
    form.fields["date"].initial = aggregated_portfolio.start_date
    if form.is_valid():
        form.save()
        return HttpResponseRedirect('/allocation/')
    return render(request, 'allocation/form_portfolio_asset.html', {'form': form})


@login_required(login_url='/registration/login/')
def update_asset_portfolio(request, pk):
    portfolio_asset = get_object_or_404(PortfolioAsset, pk=pk)
    form = PortfolioAssetForm(request.POST or None, instance=portfolio_asset)
    if form.is_valid():
        form.save()
        return HttpResponseRedirect('/allocation/')
    return render(request, 'allocation/form_portfolio_asset.html', {'form': form})


@login_required(login_url='/registration/login/')
def delete_portfolio_asset(request, pk):
    portfolio_asset = get_object_or_404(PortfolioAsset, pk=pk)
    if request.method == 'POST':
        portfolio_asset.delete()
        return HttpResponseRedirect('/allocation/')
    return render(request, 'allocation/confirm_delete.html', {'object': portfolio_asset})


@login_required(login_url='/registration/login/')
def index(request):
    if ObjectiveSolution.objects.filter(objective__user=request.user):
        return HttpResponseRedirect('allocation/viewObjectivesAllocation/')
    else:
        objectives = Objective.objects.filter(user=request.user).order_by('priority')
        resources = UserResource.objects.filter(user=request.user).order_by()
        portfolio = AggregatedPortfolio.objects.filter(user=request.user).order_by()
        if portfolio:
            asset_portfolio = PortfolioAsset.objects.filter(aggregated_portfolio=portfolio).order_by()
            prices = Series.objects.filter(asset__portfolioasset__aggregated_portfolio=portfolio, date=today)
            initial_prices = Series.objects.filter(asset__portfolioasset__aggregated_portfolio=portfolio,
                                                   date__lte=portfolio.first().start_date).order_by('-date')
            #print initial_prices.values()
            asset_series = Series.objects.filter(asset__portfolioasset__aggregated_portfolio=portfolio,
                                                 date__range=(portfolio.first().start_date, today))
            asset_series_dict = dict()
            for ap in asset_portfolio:
                asset_series_dict[ap.asset.codec] = pd.DataFrame(list(
                    asset_series.filter(asset=ap.asset).values()))

            value = portfolio_value(asset_portfolio, prices)
            initial_value = portfolio_value(asset_portfolio, initial_prices)
            weights = portfolio_composition(asset_portfolio, initial_prices)
            risks, corr = risk_corr(asset_series_dict)
            p_risk = portfolio_risk(risks, corr, weights)
            an_returns, ab_returns = return_assets(asset_series_dict, portfolio.first().start_date, today)
            annualized_r, absolute_r = portfolio_return(weights, an_returns, ab_returns)
            context = {
                'objectives': objectives,
                'resources': resources,
                'portfolio': portfolio,
                "assetPortfolio": asset_portfolio,
                "weights": {k: weights[k]*100 for k in an_returns},
                "prices": prices,
                "value": value,
                "initial_value": initial_value,
                "initial_prices": initial_prices,
                "portfolio_absolute_return": absolute_r,
                "portfolio_annualized_return": annualized_r,
                "portfolio_risk": p_risk,
                "assets_annualized_return": an_returns,
                "assets_absolute_return": ab_returns,
                "assets_risk": risks,
                "asset_correlation": corr,
            }
        else:
            context = {
                'objectives': objectives,
                'resources': resources,
            }
        return render(request, 'allocation/index.html', context)


# @login_required(login_url='/registration/login/')
# def objectives_allocation_fun(request):
#     objectives = Objective.objects.filter(user=request.user).order_by('time_horizon')
#     resources = UserResource.objects.filter(user=request.user).order_by()
#     yearly_savings = resources.first().monthly_savings*12
#     objectives = objectives_query_set_minus_savings_to_dict(objectives, yearly_savings)
#     portfolio = AggregatedPortfolio.objects.filter(user=request.user).order_by()
#     if portfolio:
#         correlation_assets = dict()
#         assets = dict()
#         asset_portfolio = PortfolioAsset.objects.filter(aggregated_portfolio=portfolio).order_by()
#         prices = Series.objects.filter(asset__portfolioasset__aggregated_portfolio=portfolio, date=today)
#
#         for ap in asset_portfolio:
#             assets[ap.asset.codec] = {
#                 "price": prices.filter(asset=ap.asset).first().price,
#                 "max_quote": ap.quote,
#                 "min_quote": 0,
#                 "statistics": dict(),
#             }
#
#         for obKey in objectives:
#             start_date = difference_date(today, objectives[obKey]["time_horizon"])
#             asset_series = Series.objects.filter(asset__portfolioasset__aggregated_portfolio=portfolio,
#                                                  date__range=(start_date, today))
#             asset_series_dict = dict()
#             for ap in asset_portfolio:
#                 asset_series_dict[ap.asset.codec] = pd.DataFrame(list(
#                     asset_series.filter(asset=ap.asset).values()))
#
#             risks, corr = risk_corr(asset_series_dict, start_date, today)
#             an_returns, ab_returns = return_assets(asset_series_dict, portfolio.first().start_date, today)
#             for rkey in risks:
#                 statistic = {
#                     "risk": risks[rkey]/100,
#                     "annualized_return": an_returns[rkey]/100
#                 }
#                 assets[rkey]["statistics"][objectives[obKey]["time_horizon"]] = statistic
#
#             correlation_assets[objectives[obKey]["time_horizon"]] = corr
#         solutions, info = objectives_allocation(correlation_assets, objectives, assets)
#         print info
#         import json
#         print json.dumps(solutions, indent=2)
#         for obk in solutions:
#             sol = ObjectiveSolution(savings_required=solutions[obk]["savings_required"], objective_id=obk)
#             sol.save()
#             if "quotes" in solutions[obk]:
#                 for ak in solutions[obk]["quotes"]:
#                     ob_port_asset = ObjectivePortfolioAsset(objective_solution=sol, asset_id=ak, quote=solutions[obk]["quotes"][ak], date=today)
#                     ob_port_asset.save()
#
#     return HttpResponseRedirect("/allocation/view_objective_allocation")


@login_required(login_url='/registration/login/')
def objectives_allocation_fun(request):
    objectives = Objective.objects.filter(user=request.user).order_by('time_horizon')
    resources = UserResource.objects.filter(user=request.user).order_by()
    yearly_savings = resources.first().monthly_savings*12
    objectives = objectives_query_set_minus_savings_to_dict(objectives, yearly_savings)
    portfolio = AggregatedPortfolio.objects.filter(user=request.user).order_by()
    if portfolio:
        asset_portfolio = PortfolioAsset.objects.filter(aggregated_portfolio=portfolio).order_by()
        prices = Series.objects.filter(asset__portfolioasset__aggregated_portfolio=portfolio, date=today)

        prices_dict = dict()
        max_quotes = dict()
        for ap in asset_portfolio:
            max_quotes[ap.asset.codec] = ap.quote
            prices_dict[ap.asset.codec] = prices.filter(asset__codec=ap.asset.codec).first().price

        risks_dict = dict()
        returns_dict = dict()
        corr_dict = dict()
        initial_prices = dict()

        for obKey in objectives:
            start_date = difference_date(today, objectives[obKey]["time_horizon"])
            print "start date", start_date
            print "week", start_date.weekday()
            while start_date.weekday() > 4:
                print "qui"
                start_date += relativedelta(days=-1)

            print "start date1", start_date
            in_prices = Series.objects.filter(asset__portfolioasset__aggregated_portfolio=portfolio,
                                              date=start_date).order_by('-date')

            prices_vett = dict()
            for ap in asset_portfolio:
                prices_vett[ap.asset.codec] = in_prices.filter(asset=ap.asset).first().price
            initial_prices[objectives[obKey]["time_horizon"]] = prices_vett

            asset_series = Series.objects.filter(asset__portfolioasset__aggregated_portfolio=portfolio,
                                                 date__range=(start_date, today))
            asset_series_dict = dict()
            for ap in asset_portfolio:
                asset_series_dict[ap.asset.codec] = pd.DataFrame(list(
                    asset_series.filter(asset=ap.asset).values()))

            risks, corr = risk_corr(asset_series_dict)
            an_returns, ab_returns = return_assets(asset_series_dict, start_date, today)
            risks_dict[objectives[obKey]["time_horizon"]] = risks
            returns_dict[objectives[obKey]["time_horizon"]] = an_returns
            corr_dict[objectives[obKey]["time_horizon"]] = corr
        solutions = optimize_ob(objectives, returns_dict, risks_dict, corr_dict,
                                initial_prices, max_quotes, prices_dict)
        #print json.dumps(solutions, indent=2)
        for obk in solutions:
            if "solution" in solutions[obk]:
                #print solutions[obk]["solution"]
                sol = ObjectiveSolution(feasible=solutions[obk]["solution"]["feasible"],
                                        savings_required=solutions[obk]["savings_required"], objective_id=obk,
                                        expected_return=solutions[obk]["solution"]["expected_return"],
                                        expected_risk=solutions[obk]["solution"]["expected_risk"])
                sol.save()
                if "quotes" in solutions[obk]["solution"]:
                    for ak in solutions[obk]["solution"]["quotes"]:

                        ob_port_asset = ObjectivePortfolioAsset(objective_solution=sol, asset_id=ak,
                                                                quote=solutions[obk]["solution"]["quotes"][ak],
                                                                date=today)
                        ob_port_asset.save()

    return HttpResponseRedirect("/allocation/viewObjectivesAllocation")


@login_required(login_url='/registration/login/')
def delete_solution(request, pk):
    obs = get_object_or_404(ObjectiveSolution, pk=pk)
    if request.method == 'POST':
        obs.delete()
        return HttpResponseRedirect('/allocation/view_objective_allocation/')
    return render(request, 'allocation/confirm_delete.html', {'object': obs})


@login_required(login_url='/registration/login/')
def delete_all_solution(request):
    solutions = ObjectiveSolution.objects.filter(objective__user=request.user)
    for solution in solutions:
        solution.delete()
    return HttpResponseRedirect('/allocation/')


@login_required(login_url='/registration/login/')
def view_objective_allocation(request):
    portfolio_user = PortfolioAsset.objects.filter(aggregated_portfolio__user=request.user)
    objective_solution = ObjectiveSolution.objects.filter(objective__user=request.user)
    portfolios = dict()
    values = dict()
    prices_dict = dict()
    return_annu = dict()
    weights = dict()
    risks_sol = dict()
    return_sol = dict()
    p_risk = dict()
    quotes_used = dict()
    quotes_remaining = dict()
    for os in objective_solution:
        portfolio = ObjectivePortfolioAsset.objects.filter(objective_solution=os)
        if portfolio:
            quotes = dict()
            for assetP in portfolio:
                quotes[assetP.asset] = assetP.quote
                if assetP.asset.codec in quotes_used:
                    quotes_used[assetP.asset.codec] += assetP.quote
                else:
                    quotes_used[assetP.asset.codec] = assetP.quote

            start_date = difference_date(today, os.objective.time_horizon)
            while start_date.weekday() > 4:
                start_date += relativedelta(days=-1)
            print start_date

            portfolios[os.id] = portfolio
            prices = Series.objects.filter(asset__objectiveportfolioasset__objective_solution_id=os.id, date=today)
            initial_prices = Series.objects.filter(asset__objectiveportfolioasset__objective_solution_id=os.id,
                                                   date=start_date)
            prices_dict[os.id] = prices
            values[os.id] = portfolio_value(portfolios[os.id], prices)
            weights[os.id] = portfolio_composition(portfolios[os.id], prices)
            weights_in = portfolio_composition(portfolios[os.id], initial_prices)

            asset_series = Series.objects.filter(asset__objectiveportfolioasset__objective_solution=os,
                                                 date__range=(start_date, today))
            asset_series_dict = dict()
            for ap in portfolio:
                asset_series_dict[ap.asset.codec] = pd.DataFrame(list(
                    asset_series.filter(asset=ap.asset).values()))
            print asset_series_dict
            risks, corr = risk_corr(asset_series_dict)
            risks_sol[os.id] = risks
            an_returns, ab_returns = return_assets(asset_series_dict, start_date, today)
            return_annu[os.id] = portfolio_return(weights_in, an_returns, ab_returns)[0]
            return_sol[os.id] = an_returns
            p_risk[os.id] = portfolio_risk(risks, corr, weights_in)
    for p in portfolio_user:
        quotes_remaining[p.asset.codec] = p.quote - quotes_used[p.asset.codec]
    print json.dumps(risks_sol, indent=2)
    print json.dumps(return_annu, indent=2)

    x_values, y_values = zip(*values.items())
    x_values = [get_object_or_404(ObjectiveSolution, pk=i).objective.finality for i in x_values]
    v_tot_values = sum(y_values)
    y_values = [v/v_tot_values*100 for v in y_values]


    chartdata1 = {
        'x': x_values,
        'y': y_values,
        'extra': {
            'x_is_date': False,
            'x_axis_format': '',
            'tag_script_js': True,
            'jquery_on_ready': False,
            "tooltip": {"y_start": "", "y_end": "%"},
        }
    }

    chartdata = {
        'x': ["a", "b", "c"],
        'y': [20, 30, 50],
        'extra': {
            'x_is_date': False,
            'x_axis_format': '',
            'tag_script_js': True,
            'jquery_on_ready': False,
            "tooltip": {"y_start": "", "y_end": "%"},
            'show_labels': False,
        }
    }
    charttype = "pieChart"
    chartcontainer1 = 'piechart_container_1'
    chartcontainer = 'piechart_container'

    context = {
        "portfolio_user": portfolio_user,
        "objective_solution": objective_solution,
        "portfolios": portfolios,
        "values": values,
        "prices": prices_dict,
        "return": return_annu,
        "risk": p_risk,
        "weights": weights,
        "risks": risks_sol,
        "returns": return_sol,
        "quotes_used": quotes_used,
        "quotes_remaining": quotes_remaining,
        'charttype': charttype,
        'chartdata1': chartdata1,
        'chartdata': chartdata,
        'chartcontainer': chartcontainer,
        'chartcontainer1': chartcontainer1,
    }

    return render_to_response("allocation/view_objective_allocation.html", context)
