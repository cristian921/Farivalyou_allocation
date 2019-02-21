from platypus import *
import json


def objectives_allocation(corr, objectives_x, assets):
    print json.dumps(assets, indent=2)
    objectives = {k: v for k, v in objectives_x.iteritems() if v["value_minus_savings"] != 0}

    def funct(quotes):
        sub_portfolio_values = []
        weight_matrix = []

        for k in range(0, len(objectives)):
           # print "*******Objective", k, "***********"
            row_quotes = quotes[k * len(assets):(k + 1) * len(assets)]
            #print "Row quotes", row_quotes
            sub_portfolio_value = 0
            j = 0
            for ak in assets:
                sub_portfolio_value += assets[ak]["price"] * row_quotes[j]
                j += 1
            weight_r = []
           # print "portfolio value", sub_portfolio_value
            prices = []
            sub_portfolio_values.append(sub_portfolio_value)
            j = 0
            for ak in assets:
                prices.append(assets[ak]["price"])
                weight_r.append(row_quotes[j] * assets[ak]["price"] / sub_portfolio_value)
                j += 1
            weight_matrix.append(weight_r)
            #print "prices", prices
            #print "pesi riga", weight_r
            #print "********************************"
        constraints = []
        j = 0
        for obk in objectives:
           # print "********Constarints", obk, "***********"
            z = 0
            k = 0
            for ak in assets:
                z += assets[ak]["statistics"][objectives[obk]["time_horizon"]]["annualized_return"] * weight_matrix[j][k]
                k += 1
            #print z, objectives[obk]["time_horizon"]
            #constraints.append(round((1 + z) ** objectives[obk]["time_horizon"] * sub_portfolio_values[j], 0))
            constraints.append(round((1 + z) ** objectives[obk]["time_horizon"] * sub_portfolio_values[j], 0))
           # print "return", z
            #print "future value", round((1 + z) ** objectives[obk]["time_horizon"] * sub_portfolio_values[j], 0)
            j += 1
           # print "********************************"
        risk_functions = []
        j = 0
        for obk in objectives:
            y1 = 0
            k = 0
            for ak in assets:
                y1 += weight_matrix[j][k] ** 2 * assets[ak]["statistics"][objectives[obk]["time_horizon"]]["risk"] ** 2
                k += 1

            y2 = 0

            p = 0
            for ak in assets:
                q = 0
                for ak1 in assets:
                    if ak != ak1:
                        y2 += weight_matrix[j][p] * weight_matrix[j][q] * \
                              assets[ak]["statistics"][objectives[obk]["time_horizon"]]["risk"] \
                              * assets[ak1]["statistics"][objectives[obk]["time_horizon"]]["risk"] * \
                              corr[objectives[obk]["time_horizon"]][ak][ak1]
                    q += 1
                p += 1

            risk_functions.append((y1 + y2)**(1.0/2.0))

        for k in range(0, len(assets)):
            s = 0
            for j in range(0, len(objectives)):
                s += quotes[k + j * len(assets)]
            constraints.append(round(s, 0))
        return risk_functions, constraints

    types = []
    for j in range(0, len(objectives)):
        for ak in assets:
            types.append(Real(assets[ak]["min_quote"], assets[ak]["max_quote"]))

    #problem = Problem(len(objectives)*len(assets), len(objectives), len(assets) + 2*len(objectives))
    problem = Problem(len(objectives)*len(assets), len(objectives), len(assets) + len(objectives))
    problem.types[:] = types
   # for x in problem.types:
       # print x

    k = 0
    for obk in objectives:
        #problem.constraints[2*k] = ">= " + str(objectives[obk]["value_minus_savings"] * 0.99)
        #problem.constraints[2*k+1] = "<= " + str(objectives[obk]["value_minus_savings"] * 1.01)
        problem.constraints[k] = ">= " + str(objectives[obk]["value_minus_savings"])
        k += 1

    #k = 2*k
    for ak in assets:
        problem.constraints[k] = "<= " + str(assets[ak]["max_quote"])
        k += 1

    problem.function = funct

    algorithm = PESA2(problem)

    algorithm.run(10000)

    feasible_solutions = [s for s in algorithm.result if s.feasible]
    if len(feasible_solutions) > 0:
        info = "feasible"
        ob = feasible_solutions[0].variables
        print feasible_solutions[0].variables
        print feasible_solutions[0].constraints
        print feasible_solutions[0].objectives
    else:
        info = "not feasible"
        ob = algorithm.result[0].variables
        print algorithm.result[0].variables
        print algorithm.result[0].constraints
        print algorithm.result[0].objectives

    i = 0
    for obk in objectives:
        j = 0
        quote_portfolio = dict()
        for ak in assets:
            quote_portfolio[ak] = ob[i*len(assets)+j]
            j += 1
        objectives_x[obk]["quotes"] = quote_portfolio
        i += 1

    return objectives_x, info
