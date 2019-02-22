from platypus import *
from utils import *
import collections


def allocation(returns, risks, corr, initial_prices, time, value, max_quotes, actual_prices):

    def functions(q):
        weights = get_weights(q, initial_prices)
        constraints = [a for a in q]
        constraints.append((return_portfolio(returns, weights)+1)**time * portfolio_value(actual_prices, q))
        constraints.append((return_portfolio(returns, weights)+1)**time * portfolio_value(actual_prices, q))
        constraints.append(return_portfolio(returns, weights))
        return [risk_portfolio(weights, risks, corr), sum(q)], constraints

    problem = Problem(len(max_quotes), 2, len(max_quotes)+3)
    i = 0
    for asset in max_quotes:
        problem.types[i] = Real(0, max_quotes[asset])
        i += 1

    problem.constraints[0:len(max_quotes)] = ">= 5"
    problem.constraints[len(max_quotes)] = ">="+str(value * 0.98)
    problem.constraints[len(max_quotes)+1] = "<="+str(value * 1.02)
    problem.constraints[len(max_quotes)+2] = ">=" + str(0.01)
    problem.function = functions

    algorithm = PAES(problem)
    algorithm.run(10000)

    feasible_solutions = [s for s in algorithm.result if s.feasible]

    return [feasible_solutions, algorithm.result]


def all_gt_ten(quotes):
    for asset in quotes:
        if quotes[asset] < 5:
            return False
    return True


def diff_quotes(quotes_1, quotes_2):
    i = 0
    for asset in quotes_1:
        val = quotes_1[asset] - quotes_2[i]
        if val > 10:
            quotes_1[asset] -= quotes_2[i]
        else:
            del quotes_1[asset]
        i += 1
    return quotes_1


import json


def optimize_ob(objectives, returns, risks, corr, initial_prices, max_quotes, actual_price):
   # print "max_quotes", max_quotes
#    print "returns", json.dumps(returns, indent=2)
  #  print "risks", json.dumps(risks, indent=2)
  #  print "initial price", json.dumps(initial_prices, indent=2)
 #   print "corr", corr
  #  print "actual price", actual_price

    for key in returns:
        returns[key] = collections.OrderedDict(sorted(returns[key].items()))
        risks[key] = collections.OrderedDict(sorted(risks[key].items()))
        initial_prices[key] = collections.OrderedDict(sorted(initial_prices[key].items()))
    max_quotes = collections.OrderedDict(sorted(max_quotes.items()))
    for obk in objectives:
        if len(max_quotes) > 0:
            sols = allocation(returns[objectives[obk]["time_horizon"]], risks[objectives[obk]["time_horizon"]],
                              corr[objectives[obk]["time_horizon"]], initial_prices[objectives[obk]["time_horizon"]],
                              objectives[obk]["time_horizon"], objectives[obk]["value_minus_savings"],
                              max_quotes, actual_price)
            if sols[0]:
                feasible = True
                sol = sols[0][0]
            else:
                feasible = False
                sol = sols[1][0]
           # print "value objective", objectives[obk]["value_minus_savings"]
         #   print "quote", sol.variables
          #  print "constraints", sol.constraints
          #  print "objectives", sol.objectives
            sol_quote = dict()
            i = 0
            for asset in max_quotes:
                sol_quote[asset] = sol.variables[i]
                i += 1

            objectives[obk]["solution"] = {
                "quotes": sol_quote,
                "expected_return": sol.constraints[len(sol.constraints)-1],
                "expected_risk": sol.objectives[0],
                "feasible": feasible,
            }

            i = 0
            for asset in max_quotes:
                val = max_quotes[asset] - sol.variables[i]
                if val > 10:
                    max_quotes[asset] -= sol.variables[i]
                else:
                    #print "deleted", asset
                    del max_quotes[asset]
                    for obk1 in objectives:
                        del risks[objectives[obk1]["time_horizon"]][asset]
                        del returns[objectives[obk1]["time_horizon"]][asset]
                        del initial_prices[objectives[obk1]["time_horizon"]][asset]
                    del actual_price[asset]
                i += 1
    return objectives
