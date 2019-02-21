from django import forms
from .models import *


class AggregatedPortfolioForm(forms.ModelForm):
    class Meta:
        model = AggregatedPortfolio
        fields = ['name', 'user', 'start_date']
        widgets = {
            'start_date': forms.DateInput(attrs={'class': 'datepicker'}),
            'user': forms.HiddenInput()
        }


class PortfolioAssetForm(forms.ModelForm):

    class Meta:
        model = PortfolioAsset
        fields = ['aggregated_portfolio', 'asset', 'date', 'quote']
        widgets = {
            'aggregated_portfolio': forms.HiddenInput(),
            'date': forms.HiddenInput(),
            'asset': forms.Select(choices=Asset.objects.all())
        }
        labels = {'price': 'price'}

        price = forms.Field(
            widget=forms.FloatField(),
            label='price',
            help_text='price',
        )


class ObjectiveForm(forms.ModelForm):
    class Meta:
        model = Objective
        fields = ['user', 'finalValue', 'time_horizon', 'finality', 'priority']
        widgets = {
            'user': forms.HiddenInput()
        }


class ResourcesForm(forms.ModelForm):
    class Meta:
        model = UserResource
        fields = ['founds', 'monthly_savings', 'user']
        widgets = {
            'user': forms.HiddenInput()
        }
