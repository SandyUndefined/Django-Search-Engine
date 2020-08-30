from django.shortcuts import render, redirect
from SearchEngine.search import google,yahoo,duck,ecosia


def homepage(request):
    return render(request,'home.html')


def results(request):
    if request.method == "POST":
        result = request.POST.get('search')
        google_data = google(result)
        yahoo_data = yahoo(result)
        duck_data = duck(result)
        ecosia_data = ecosia(result)
        if result == '':
            return redirect('Home')
        else:
            return render(request,'results.html',{'google': google_data, 'yahoo': yahoo_data, 'duck': duck_data, 'ecosia': ecosia_data})