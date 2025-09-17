from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth.decorators import login_required

# Create your views here.
@login_required
def tichhop(request):
    return render(request, 'pages/Tichhop/tichhop.html')
@login_required
def tvoff(request):
    return render(request, 'pages/Tichhop/tvoff.html')
@login_required
def thietbi(request):
    return render(request, 'pages/Tichhop/thietbi.html')
@login_required
def tatthongbao(request):
    return render(request, 'pages/Tichhop/tatthongbao.html')
@login_required
def ngaygio(request):
    return render(request, 'pages/Tichhop/ngaygio.html')
@login_required
def manhinhxanh(request):
    return render(request, 'pages/Tichhop/manhinhxanh.html')
@login_required
def fileusb(request):
    return render(request, 'pages/Tichhop/fileusb.html')
@login_required
def khongwifi(request):
    return render(request, 'pages/Tichhop/khongwifi.html')
@login_required
def docamung(request):
    return render(request, 'pages/Tichhop/docamung.html')