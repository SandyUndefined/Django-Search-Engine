from django.http import HttpResponse
from django.shortcuts import render


def homepage(request):
    return render(request,'home.html')


def results(request):
    if request.method == "POST":
        result = request.POST.get('search')
        if result == '':
            return render(request,'home.html')
        else:
            return render(request,'results.html',{'data':result})