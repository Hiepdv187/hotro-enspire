from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth.decorators import login_required
# Create your views here.
@login_required
def tvbox(request):
    return render(request, 'pages/Tvbox/tvbox.html')
@login_required
def usbbox(request):
    return render(request, 'pages/Tvbox/usbbox.html')
@login_required
def sudungoff(request):
    return render(request, 'pages/Tvbox/sudungoff.html')
@login_required
def roi(request):
    return render(request, 'pages/Tvbox/roi.html')
@login_required
def phukien(request):
    return render(request,'pages/TVbox/phukien.html')
@login_required
def nhieu(request):
    return render(request, 'pages/Tvbox/nhieu.html')
@login_required
def ngaytvbox(request):
    return render(request, 'pages/Tvbox/ngaytvbox.html')
@login_required
def khonglen(request):
    return render(request, 'pages/TVbox/khonglen.html')
@login_required
def ketnoi(request):
    return render(request, 'pages/Tvbox/ketnoi.html')
@login_required
def dophangiai(request):
    return render(request, 'pages/Tvbox/dophangiai.html')
@login_required
def camung(request):
    return render(request, 'pages/Tvbox/camung.html')