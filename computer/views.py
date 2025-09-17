from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth.decorators import login_required

# Create your views here.
@login_required
def pc(request):
    return render(request, 'pages/PC/pc.html')
@login_required
def xemthongso(request):
    return render(request, 'pages/PC/xemthongso.html')
@login_required
def manhinhxanhpc(request):
    return render(request, 'pages/PC/manhinhxanhpc.html')
@login_required
def khongmangpc(request):
    return render(request, 'pages/PC/khongmangpc.html')
@login_required
def khonglenman(request):
    return render(request, 'pages/PC/khonglenman.html')
@login_required
def khongbatduoc(request):
    return render(request, 'pages/PC/khongbatduoc.html')
@login_required
def hoanchinh(request):
    return render(request, 'pages/PC/hoanchinh.html')
@login_required
def giatlag(request):
    return render(request, 'pages/PC/giatlag.html')