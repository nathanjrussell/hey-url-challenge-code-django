from django.shortcuts import render,redirect
from django.http import HttpResponse, HttpResponseNotFound, JsonResponse
from .models import Url, Click

from .forms import UrlForm
from django.utils.timezone import now
from string import ascii_lowercase, ascii_uppercase
from string import digits as ascii_digits
from django.contrib import messages
from django.db.models import Count
import json

def index(request):
    urls = Url.objects.order_by('-created_at')
    context = {'urls': urls}
    return render(request, 'heyurl/index.html', context)

def store(request):
    # FIXME: Insert a new URL object into storage
    if request.method=="POST":
        cdate = now()
        f = UrlForm(request.POST)
        if f.is_valid():
            newurl = f.save(commit=False)
            newurl.created_at = cdate
            newurl.updated_at = cdate
            newurl.save()
            rowpk = newurl.pk - 1
            shorturl = ""
            symbols = ascii_lowercase + ascii_digits + ascii_uppercase
            while rowpk > 0:
                rowpk, r = divmod(rowpk, 62)
                shorturl += symbols[r]
            newurl.short_url = shorturl
            newurl.save()
            msg = "The URL ({0!s}) was successfully uploaded to the database. It is identified by the short URL tag ({1!s}).".format(newurl.original_url,shorturl)
            messages.add_message(request, messages.SUCCESS, msg)
            return redirect('index')
        else:
            messages.error(request, f.errors)
            return redirect('index')

    else:
        return redirect('index')


def short_url(request, short_url):
    # FIXME: Do the logging to the db of the click with the user agent and browser
    cdate = now()
    try:
        r = Url.objects.get(short_url=short_url)
        r.clicks += 1
        r.updated_at = cdate
        r.save()
    except:
        context = {}
        context['header'] = "Oops! - 404 Error"
        context['lead'] = "Something Went Wrong"
        context['msg'] = "The short URL, identifed by the tag ({0!s}), was not found in the database.".format(short_url)
        output = render(request, 'heyurl/response.html', context)
        return HttpResponseNotFound(output)

    try:
        c = Click(url=r)
        c.platform = request.user_agent.os.family
        c.browser = request.user_agent.browser.family
        c.created_at = cdate
        c.updated_at = cdate
        c.save()
    except:
        #clever error logging using cloud application (AWS logging)
        pass

    return redirect(r.original_url)

def click_data(request, short_url):
    cdate = now()
    try:
        u = Url.objects.get(short_url=short_url)
    except:
        context = {}
        context['header'] = "Oops!"
        context['lead'] = "That Short URL Does Not Exist"
        context['msg'] = "The short URL, identifed by the tag ({0!s}), was not found in the database.".format(short_url)
        return render(request,'heyurl/response.html',context)

    c = Click.objects.filter(url_id=u, created_at__month=cdate.month,created_at__year=cdate.year).values('created_at__day','browser','platform','created_at')

    if c.count() == 0:
        context = {}
        context['header'] = "No Click Data Available!"
        context['lead'] = "The database is unable to provide click data for this short URL tag."
        context['msg'] = "The short URL, identifed by the tag ({0!s}), was found in the database. However, click data is not available for this Short URL tag.".format(short_url)
        return render(request,'heyurl/response.html',context)

    day_totals =Click.objects.filter(url_id=u,created_at__month=cdate.month,created_at__year=cdate.year).values("created_at__day").annotate(dcount=Count('created_at__day'))
    daily_count_list = [0]*(cdate.day+1)
    for r in day_totals:
        daily_count_list[r['created_at__day']-1] = r['dcount']
    click_log = []
    for r in c:
        tmp = {}
        tmp['Date'] = r['created_at'].strftime("%m/%d/%Y")
        tmp['Time'] = r['created_at'].strftime("%H:%M:%S")
        tmp['browser'] = r['browser']
        tmp['platform'] = r['platform']
        click_log.append(tmp)

    data = {}
    data['click_log'] = click_log
    data['daily_count_list'] = daily_count_list
    for header_type in ['browser','platform']:
        rows = Click.objects.filter(url_id=u,created_at__month=cdate.month,created_at__year=cdate.year).values('created_at__day',header_type).annotate(dcount=Count('created_at__day')).order_by('created_at__day')
        tmp_list = []
        for r in rows:
            tmp = {}
            dtot = daily_count_list[r['created_at__day']-1]
            clicks = r['dcount']
            tmp[header_type] = r[header_type]
            tmp['Date'] = r['created_at__day']
            tmp['Clicks'] = clicks
            tmp['Percentage'] = round(100*clicks/dtot,1)
            tmp_list.append(tmp)
        data[header_type] = tmp_list

    dstr = json.dumps(data)
    context = {}
    context['categories'] = ['browser','platform']
    context['data'] = dstr
    return render(request,'heyurl/click_data.html',context)

def get_n_urls(request,num_records=0):
    result = {}
    data = []
    includes = []
    url_rows=Url.objects.all().order_by('-created_at')
    if num_records > 0:
        url_rows = url_rows[:num_records]
    else:
        return JsonResponse({"data" : [], "included": [] })
    for r in url_rows:
        attributes = {}
        tmp = {'type':'urls'}
        tmp['id'] = r.pk
        attributes['created_at'] = r.created_at
        attributes['updated_at'] = r.updated_at
        attributes['original_url'] = r.original_url
        attributes['short_url'] = request.META['HTTP_HOST'] + "/u/"+r.short_url
        attributes['clicks'] = r.clicks
        tmp['attributes'] = attributes
        relationships = {}
        metrics = {}
        metric_data = []
        clicks = Click.objects.filter(url=r).order_by('-created_at')
        for c in clicks:
            tmp2 = {'type':'metrics'}
            tmp2['id'] = c.pk
            metric_data.append(tmp2)
            metric_attributes = {}
            metric_attributes['browser'] = c.browser
            metric_attributes['platform'] = c.platform
            metric_attributes['created_at'] = c.created_at
            metric_attributes['updated_at'] = c.updated_at
            tmp2['attributes'] = metric_attributes
            self_url = request.META['HTTP_HOST'] + "/api/metrics/" + str(c.pk)
            tmp2['links'] = {'self':self_url}
        metrics['data'] = metric_data
        relationships['metrics'] = metrics
        tmp['relationships'] = relationships
        data.append(tmp)
    result['data'] = data
    result['included'] = includes
    return JsonResponse(result)
