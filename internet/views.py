from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth.decorators import login_required

# Create your views here.
@login_required
def mang(request):
    return render(request, 'pages/Mangvawifi/mang.html')
@login_required
def mangday(request):
    return render(request, 'pages/Mangvawifi/mangday.html')
@login_required
def thietbimang(request):
    return render(request, 'pages/Mangvawifi/thietbimang.html')
@login_required
def modem(request):
    return render(request, 'pages/Mangvawifi/modem.html')
@login_required
def wifi(request):
    return render(request, 'pages/Mangvawifi/wifi.html')