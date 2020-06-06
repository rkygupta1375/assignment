from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.detail import DetailView 
from django.views.generic.list import ListView
from django.views.generic.edit import FormView 

class Homepage(LoginRequiredMixin,ListView):
    pass
