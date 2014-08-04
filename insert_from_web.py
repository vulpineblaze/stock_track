#!/usr/bin/python
import ycs_apps.settings
# art_apps.settings.configure()
import os
import sys

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ycs_apps.settings")
    
from django.db import models
from django.db import connection
from django.contrib.auth.models import User
from django.core.exceptions import MultipleObjectsReturned

from ycs_apps.stock_track.models import *

from ycs_apps.stock_track import views
from ycs_apps.stock_track import forms
from ycs_apps.stock_track import tests




from django.utils import timezone
from datetime import *
import _strptime

import pytz

from xml.dom import minidom
import urllib

import csv
import urllib2
import StringIO

import threading


HOW_MANY_COMPANIES = 0 # Zero means infinite
MAX_THREADS = 10


def thread_joiner(threads):
    """ """
    for t in threads:
        t.join()
        #try:
            #t.join()
            #print t, "did properly join()"
        #except:
            ##~ print "thread did not properly join()"
            #pass
            
    return []

def enumerate_joiner(main_thread):
    #~ main_thread = threading.currentThread()
    for t in threading.enumerate():
        if t is main_thread:
            continue
        #~ logging.debug('joining %s', t.getName())
        t.join()

def make_daily_from_row(row, company):
    """ """
    #~ print row, company
    row_date = datetime.strptime(str(row[0]) , '%Y-%m-%d')#'%b %d %Y %I:%M%p') #row[0],
    row_price_open = float(row[1])
    row_price_high = float(row[2])
    row_price_low = float(row[3])
    row_price_close = float(row[4])
    row_price_volume = float(row[5])
    row_price_adj_close = float(row[6])
    

        
    p, was_made = Daily.objects.get_or_create(
        cid_id = company.id,
        date = row_date,
        price_open = row_price_open,
        price_high = row_price_high,
        price_low = row_price_low,
        price_close = row_price_close,
        price_volume = row_price_volume,
        price_adj_close = row_price_adj_close
        )
     
    connection.close()    
    #~ return p , was_made
    
    
def make_company_from_csv(company_ticker,company_name, second_pass=False):
    # company_ticker = company.getAttribute("symbol")
    # company_name = company.getAttribute("name")
    p = created = ""

    get_company_attempt = Company.objects.filter(
                ticker=company_ticker, 
                long_name=company_name)

    if get_company_attempt:
        # print get_company_attempt, get_company_attempt[0], get_company_attempt[1]
        if get_company_attempt.count() > 1:
            # print "Found duplicate: "+str(get_company_attempt[1].ticker)
            
            for item in get_company_attempt:
                for sub_item in Daily.objects.filter(cid=item):
                    # print item, sub_item
                    sub_item.delete()
                print item, item.ticker    
                item.delete()
        elif get_company_attempt.count() == 1:
            return get_company_attempt[0], False
        # return get_company_attempt, False
    
    try:
        p, created = Company.objects.get_or_create(
            ticker=company_ticker, 
            long_name=company_name,
            modified = (datetime.now(pytz.utc) - timedelta(days=5))
            )
    except MultipleObjectsReturned as e:
        #~ print e, Company.objects.filter(ticker=company_ticker)#[1].delete()
        try:
            Company.objects.filter(ticker=company_ticker)[1].delete()
        except:
            if not second_pass:
                make_company_from_csv(company_ticker,company_name, True)
    
    connection.close()
    return p, created
     

def build_company_table_from_web():
    """ """
    
    threadLock = threading.Lock()
    threads = []
    
    url_str = 'http://query.yahooapis.com/v1/public/yql?q=select%20*%20from%20yahoo.finance.industry%20where%20id%20in%20(select%20industry.id%20from%20yahoo.finance.sectors)&env=store%3A%2F%2Fdatatables.org%2Falltableswithkeys'
    xml_str = urllib.urlopen(url_str).read()
    xmldoc = minidom.parseString(xml_str)
    
    data_set = xmldoc.getElementsByTagName('company')
    
    
    data_set_len = len(data_set)*1.0
    divisor = data_set_len / 100.0
    count = 0
    percent = 0
    index=0
    recursion = 0
    obj_list = []
    
    for company in data_set:
        count += 1
        index += 1
        recursion += 1
        
        company_ticker = company.getAttribute("symbol")
        company_name = company.getAttribute("name")

        if company_ticker in obj_list:
            continue  #basically doesnt bother with duplicates from xml
        else:
            obj_list.append(company_ticker)

        #~ f = job_server.submit(make_company_from_csv, (company,))
        #~ p, created = make_company_from_csv(company)
        
        #~ obj_list.append(p) 
        
        #~ print recursion
        if recursion > MAX_THREADS:
            recursion = 0
            #~ threads = thread_joiner(threads)
            enumerate_joiner(threading.currentThread())
            
            #~ r = f
            #~ print r
        the_thread = threading.Thread(
                    name='company_insert_'+str(count), 
                    target=make_company_from_csv,
                    args=(company_ticker,company_name)
                    )
        the_thread.start()    
        threads.append(the_thread)
     
    
        
        if (count > HOW_MANY_COMPANIES and HOW_MANY_COMPANIES > 0):
            break
                    
        if count > divisor:
            count = 1
            percent += 1
                        
            print "Insert approx "+str(percent)+"% complete, on pk: "+str(index)
        elif index > data_set_len:
            print "ERROR! Somehow the loop has exceeded the number of entries | index: "+str(index)+" , total: "+str(data_set_len)
        elif count == 0:
            print "Begining loop over "+str(data_set_len)+" entries!"
        
    
    #~ threads = thread_joiner(threads)
    enumerate_joiner(threading.currentThread())
    return ""
    
    
    
def build_ticker_data_from_web( company):
    """    """
    #~ print company.id,company.ticker,company.long_name
    
    threadLock = threading.Lock()
    threads = []
    
    now_ish = datetime.today()
    future_year = now_ish.year+1

    existing_dailies = Daily.objects.filter(cid=company)
    
    if existing_dailies.count() > 500:
        return ""
    elif existing_dailies.count() > 1:
        past_year = now_ish.year-1
        #~ print "Update for "+str(company.ticker)
    else:
        past_year = now_ish.year-70
        #~ print "New Entry for "+str(company.ticker)

    
    the_url_string ="http://real-chart.finance.yahoo.com/table.csv?s="
    the_url_string += str(company.ticker)+"&a=11&b=31&c="
    the_url_string += str(past_year)+"&d=00&e=1&f="
    the_url_string += str(future_year)+"&g=d&ignore=.csv"
    
    #~ the_url_string ="http://real-chart.finance.yahoo.com/table.csv?s="
    #~ the_url_string += str(company.ticker)+"&d=6&e=25&f="
    #~ the_url_string += str(future_year)+"&g=d&a=0&b=2&c="
    #~ the_url_string += str(past_year)+"&ignore=.csv"
    
    #~ print the_url_string
    
    #~ url = 'http://winterolympicsmedals.com/medals.csv'
    try:
        response = urllib2.urlopen(the_url_string)
        cr = csv.reader(response)
        company.activated = True
        company.save()
    except:
        company.activated = False
        company.save()
        return {}
        
    count = 0
    recursion = 0
    was_made = False
    
    #~ company.activated = True
    #~ company.save()
    
    for row in cr:
        count += 1
        recursion += 1
        
        if count == 1:
            continue
        
        #~ f = job_server.submit(make_daily_from_row, (row,))
        f=""
        
        if recursion > MAX_THREADS:
            recursion = 0
            #~ threads = thread_joiner(threads)
            enumerate_joiner(threading.currentThread())
            
            
        threads.append(
                threading.Thread(
                        name='daily_insert_'+str(count), 
                        target=make_daily_from_row,
                        args=(row, company)
                        ).start()
                )
        #~ p, was_made = make_daily_from_row(row)

        
        #~ if count > 100:
            #~ break
    
    #~ threads = thread_joiner(threads)
    enumerate_joiner(threading.currentThread())
    
    return f

    
def main():
    """ business logic for when running this module as the primary one!"""
    start_time = datetime.now()
    temp_time = datetime.now()
    bug_in_threading_workaround_date = datetime.strptime("2014-07-30", '%Y-%m-%d')
    
    
    f = build_company_table_from_web()
    #~ r = f
    #~ print r
    #~ 
    #~ build_ticker_data_from_web()
    
    obj_list = Company.objects.all()
    
    count=0
    divisor = (len(obj_list)*1.0)
    
    print "Starting processing of "+str(divisor)+" companies."
    
    for company in obj_list:
        #~ if company.id == 4:
        count += 1
        f = build_ticker_data_from_web(company)
        
        if (count > HOW_MANY_COMPANIES and HOW_MANY_COMPANIES > 0):
            break
            
        if ((datetime.now() - temp_time).seconds) > 30 :
            temp_time = datetime.now()
            print "Accomplished "+str((1.0*count/divisor)*100)+"% in "+str(((datetime.now() - start_time).seconds))+" seconds."
    #~ r = f
    #~ print r
    end_time = (datetime.now() - start_time)
    summary_string = "Final time was " + str(end_time.seconds//60%60)
    summary_string += " minutes, and " + str(end_time.seconds%60) + " seconds."
    print summary_string

# Here's our payoff idiom!
if __name__ == '__main__':
    main()
