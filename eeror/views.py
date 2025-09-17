from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth.decorators import login_required

@login_required
def index(request):
    return render(request, 'pages/eeror.html')
@login_required
def caiapp(request):
    return render(request, 'pages/Caiapp/caiapp.html')


