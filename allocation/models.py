# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.contrib.auth.models import User


class Asset(models.Model):
    codec = models.CharField(max_length=8, primary_key=True)
    name = models.CharField(max_length=200)

    def __str__(self):
        return self.name


class Series(models.Model):
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE)
    date = models.DateField()
    price = models.FloatField()


class Objective(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    finalValue = models.FloatField()
    time_horizon = models.IntegerField()
    finality = models.CharField(max_length=300)
    priority = models.IntegerField()


class AggregatedPortfolio(models.Model):
    name = models.CharField(max_length=200)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    start_date = models.DateField()


class ObjectiveSolution(models.Model):
    objective = models.ForeignKey(Objective, on_delete=models.CASCADE)
    expected_return = models.FloatField()
    expected_risk = models.FloatField()
    savings_required = models.FloatField()
    feasible = models.BooleanField()


class ObjectivePortfolioAsset(models.Model):
    objective_solution = models.ForeignKey(ObjectiveSolution, on_delete=models.CASCADE)
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE)
    date = models.DateField()
    quote = models.FloatField()


class UserResource(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    founds = models.FloatField()
    monthly_savings = models.FloatField()


class PortfolioAsset(models.Model):
    aggregated_portfolio = models.ForeignKey(AggregatedPortfolio, on_delete=models.CASCADE)
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE)
    date = models.DateField()
    quote = models.FloatField()
