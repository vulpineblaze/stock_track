#!/usr/bin/python
import ycs_apps.settings
# art_apps.settings.configure()
import os
import sys
import math

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ycs_apps.settings")
    
from django.db import models
from django.db import connection
from django.contrib.auth.models import User
from django.core.exceptions import MultipleObjectsReturned

from ycs_apps.stock_track.models import *

from ycs_apps.stock_track import views
from ycs_apps.stock_track import forms
from ycs_apps.stock_track import tests


import csv

from django.utils import timezone
from datetime import *
import _strptime
import pytz

#~ from numpy import array
import numpy as np

#~ from xml.dom import minidom
#~ import urllib
#~ 
#~ import csv
#~ import urllib2
#~ import StringIO


import threading




HOW_MANY_COMPANIES = 0 # Zero means infinite
MAX_THREADS = 10

MINIMUM_CURRENT_PRICE = 5.0
MINIMUM_CURRENT_VOLUME = 10000

CPI_DICT = {}

start_time = datetime.now()


def enumerate_joiner(main_thread):
    #~ main_thread = threading.currentThread()
    for t in threading.enumerate():
        if t is main_thread:
            continue
        #~ logging.debug('joining %s', t.getName())
        t.join()
        
def calc_inflation_by_year(year, price) : 
    """ """
    
    CPI_DICT = return_cpi_dict()
    #~ print CPI_DICT['1980']
    
    price_adjusted = 0.0
    year_diff = datetime.today().year - year
    
    try:
        if year < 1970:
            adj_percent = CPI_DICT['1970']
        else:
            adj_percent = CPI_DICT[str(year)]
    except:
        print "Year "+str(year)+" not found, using 1970"
        adj_percent = CPI_DICT['1970']
    
    price_adjusted = price * float(adj_percent)
    
    
    return price_adjusted


def calc_score_undervalue(price_list):
    """ """
    score = 0.0
    
    current = np.average(price_list[:100])
    avg = np.average(price_list)
    stdev = np.std(price_list)
    the_min = np.amin(price_list)
    the_max = np.amax(price_list)

    # if current < MINIMUM_CURRENT_PRICE:
    #     return 0.0 # score irrelevant, stock is junk
    
    if (avg-stdev < the_min or avg+stdev > the_max):
        #~ print avg, stdev, the_min, the_max, current, score
        return 0.0 # too volatile
    
    if (current < the_min or current > the_max):
        #~ print avg, stdev, the_min, the_max, current, score
        return 0.0 # error condition? bad data?
        
    if (current < avg-stdev and current > the_min):
        #~ print avg, stdev, the_min, the_max, current, score
        score = (avg-stdev)/current # the sweet spot; larger the better
        
    return score
   
   
   
def return_cpi_dict():
    """ """
    
    f = open("cpi.csv", 'rt')
    try:
        reader = csv.reader(f)
        for row in reader:
            #~ print row
            CPI_DICT[row[0]] = row[1]
    finally:
        f.close()
    
    return CPI_DICT


    
   
def analyse_and_put_in_db(company):
    """ """
    #~ print row, company
    #~ row_date = datetime.strptime(str(row[0]) , '%Y-%m-%d')#'%b %d %Y %I:%M%p') #row[0],
    #~ row_price_open = float(row[1])
    #~ row_price_high = float(row[2])
    #~ row_price_low = float(row[3])
    #~ row_price_close = float(row[4])
    #~ row_price_volume = float(row[5])
    #~ row_price_adj_close = float(row[6])
    
    price_list = []
    volume_list = []
    do_for_count = 10
    
    if company.modified:
        if company.modified.date() == datetime.now(pytz.utc).date():
            # print "This record was edited today!"
            return []
            # pass

    # else:        
    for daily in company.daily_set.filter().order_by('-date'):
        #~ print daily.date
        price_list.append(calc_inflation_by_year(
                        daily.date.year,
                        daily.price_close
                        ))
        volume_list.append(daily.price_volume)

    #~ price_array = array( price_list )
    

    if (
        len(price_list) > 100 and 
        len(volume_list) > 100 and
        np.average(volume_list[:100]) > MINIMUM_CURRENT_VOLUME and
        np.average(price_list[:100]) > MINIMUM_CURRENT_PRICE
            ):  
        company.price_average = np.average(price_list)    
        company.price_stdev = np.std(price_list) 
        company.price_min = np.amin(price_list) 
        company.price_max = np.amax(price_list) 
        company.price_median = np.median(price_list)
        company.score_undervalue = calc_score_undervalue(price_list)
        company.has_averages = True 
        company.modified = timezone.now()
        
        company.save()
         
        connection.close()    
    else:
        company.has_averages = False 
        company.modified = (datetime.now(pytz.utc) - timedelta(days=5))
        company.save()
        connection.close()   
        
            
        
        
        
def analyse_all_companies(obj_list):
    """ """
    
    threadLock = threading.Lock()
    threads = []
    
    temp_time = datetime.now()
    now_ish = datetime.today()
    future_year = now_ish.year+1
    

    divisor = (obj_list.count()*1.0)
    
    count = 0
    recursion = 0
    was_made = False
    
    for company in obj_list:
        count += 1
        recursion += 1
        
        #~ f = analyse_ticker_data_for_company(job_server,company)

        if (count > HOW_MANY_COMPANIES and HOW_MANY_COMPANIES > 0):
            break
            
        if ((datetime.now() - temp_time).seconds) > 30 :
            temp_time = datetime.now()
            print "Accomplished "+str((1.0*count/divisor)*100)+"% in "+str(((datetime.now() - start_time).seconds))+" seconds."
        
        if recursion > MAX_THREADS:
            recursion = 0
            enumerate_joiner(threading.currentThread())
            
            
        threads.append(
                threading.Thread(
                        name='daily_insert_'+str(count), 
                        target=analyse_and_put_in_db,
                        args=(company,)
                        ).start()
                )

    enumerate_joiner(threading.currentThread())

def main():
    """ business logic for when running this module as the primary one!"""
    
    
    bug_in_threading_workaround_date = datetime.strptime("2014-07-30", '%Y-%m-%d')
        

    
    obj_list = Company.objects.all()
    
    
    print "Starting processing of "+str(obj_list.count())+" companies."
    
    analyse_all_companies(obj_list)
    
   

    end_time = (datetime.now() - start_time)
    summary_string = "Final time was " + str(end_time.seconds//60%60)
    summary_string += " minutes, and " + str(end_time.seconds%60) + " seconds."
    print summary_string

# Here's our payoff idiom!
if __name__ == '__main__':
    main()
