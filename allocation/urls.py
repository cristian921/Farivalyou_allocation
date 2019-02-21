from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^addAggregatedPortfolio/$', views.add_aggregated_portfolio, name='aggregated_portfolio_form'),
    url(r'^(?P<pk>[0-9]+)/deleteAggregatedPortfolio/$', views.delete_aggregated_portfolio, name='delete_aggregated_portfolio'),
    url(r'^(?P<pk>[0-9]+)/addAssetPortfolio/$', views.add_asset_portfolio, name='add_asset_portfolio'),
    url(r'^(?P<pk>[0-9]+)/deletePortfolioAsset/$', views.delete_portfolio_asset, name='delete_portfolio_asset'),
    url(r'^(?P<pk>[0-9]+)/updatePortfolioAsset/$', views.update_asset_portfolio, name='delete_portfolio_asset'),
    url(r'^addObjective/$', views.add_objective, name="add_objective"),
    url(r'^(?P<pk>[0-9]+)/updateObjective/$', views.update_objective, name='update_objective'),
    url(r'^(?P<pk>[0-9]+)/deleteObjective/$', views.delete_objective, name='delete_objective'),
    url(r'^addResources/$', views.add_resources, name="add_resources"),
    url(r'^(?P<pk>[0-9]+)/updateResources/$', views.update_resources, name="update_resources"),
    url(r'^(?P<pk>[0-9]+)/deleteResources/$', views.delete_resources, name="delete_resources"),
    url(r'^objectivesAllocation/$', views.objectives_allocation_fun, name='objectives_allocation'),
    url(r'^(?P<pk>[0-9]+)/deleteSolution/$', views.delete_solution, name="delete_solution"),
    url(r'^deleteAllSolution/$', views.delete_all_solution, name="delete_all_solution"),
    url(r'^viewObjectivesAllocation/$', views.view_objective_allocation, name="chart"),
]
