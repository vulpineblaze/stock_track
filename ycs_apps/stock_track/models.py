from django.db import models, connection

from django.contrib.auth.models import User

from datetime import *
import pytz
from django.utils import timezone

import csv
import urllib2
import StringIO

import numpy as np

from random import randint



# Create your models here.


MINIMUM_CURRENT_PRICE = 5.0
MINIMUM_CURRENT_VOLUME = 10000

CPI_DICT = {}



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



class CompanyQuerySet(models.query.QuerySet):
    """ """

    def find_acceptable_pk(self):
        """ """

        found_pk = 0
        condition = False
        reject_string = "This is an unknown symbol."

        total_objs = self.count()

        while not condition:
            rand_int = randint(1,total_objs)
            the_company = self.get(pk=rand_int)
            ticker_string = the_company.ticker
            if "." in ticker_string:
                continue



            site= "http://www.nasdaq.com/symbol/"+ticker_string
            hdr = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11',
                   'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                   'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
                   'Accept-Encoding': 'none',
                   'Accept-Language': 'en-US,en;q=0.8',
                   'Connection': 'keep-alive'}

            req = urllib2.Request(site, headers=hdr)

            try:
                page = urllib2.urlopen(req)
                content = page.read()
            except urllib2.HTTPError, e:
                print e.fp.read()
                content = None

            if content:
                if reject_string in content:
                    condition = False
                    # print "Rejected "+ticker_string
                else:
                    condition = True
                    found_pk = the_company.pk
            
        return found_pk   


class CompanyManager(models.Manager):
    '''Use this class to define methods just on Entry.objects.'''
    def get_queryset(self):
        return CompanyQuerySet(self.model)



class Company(models.Model):
    ticker = models.CharField(db_index=True,max_length=20)
    long_name = models.CharField(max_length=200)
    
    modified = models.DateTimeField(blank=True)
    
    activated = models.BooleanField(default=False)
    has_averages = models.BooleanField(default=False)
    not_traded = models.BooleanField(default=False)
    
    price_average = models.FloatField(default=0.0)
    price_stdev = models.FloatField(default=0.0)
    price_min = models.FloatField(default=0.0)
    price_max = models.FloatField(default=0.0)
    price_median = models.FloatField(default=0.0)
    
    score_undervalue = models.FloatField(default=0.0)

    objects = CompanyManager() # don't forget this


    def add_dailies_to_company(self, only_try=None,try_old_only=False):
        """ """

        now_ish = datetime.today()
        future_year = now_ish.year+1
        past_year = now_ish.year-70

        the_url_string ="http://real-chart.finance.yahoo.com/table.csv?s="
        the_url_string += str(self.ticker)+"&a=11&b=31&c="
        the_url_string += str(past_year)+"&d=00&e=1&f="
        the_url_string += str(future_year)+"&g=d&ignore=.csv"
        


        print "Get CSV"
        try:
            csv_url_opened = urllib2.urlopen(the_url_string)
            cr = csv.reader(csv_url_opened)
            self.activated = True
            self.save()
        except:
            self.activated = False
            self.save()
            return 
            
        count = 0
        count_actually_inserted = 0
        count_daily_found = 0
        centi_count = 0

        print "Daily"
        daily_queryset = Daily.objects.filter(cid=self.id)

        for row in cr:
            count += 1

            if count == 1:
                continue

            if count % 1000 == 0:
                centi_count += 1
                print str(centi_count*1000)+" Entries reviewed!"   

            if only_try:
                if count_actually_inserted > only_try:
                    break #if we insert only_try, no matter what break

                if not try_old_only:
                    if count_daily_found > 365: # only goes back a year
                        break #if new, only_try breaks on founds too

            f=""
            row_date = datetime.strptime(str(row[0]) , '%Y-%m-%d')#'%b %d %Y %I:%M%p') #row[0],
            row_price_open = float(row[1])
            row_price_high = float(row[2])
            row_price_low = float(row[3])
            row_price_close = float(row[4])
            row_price_volume = float(row[5])
            row_price_adj_close = float(row[6])


            

            if not daily_queryset.filter(date=row_date).exists():
                count_actually_inserted += 1
                p, created = Daily.objects.get_or_create(
                                    cid_id = self.id,
                                    date = row_date,
                                    price_open = row_price_open,
                                    price_high = row_price_high,
                                    price_low = row_price_low,
                                    price_close = row_price_close,
                                    price_volume = row_price_volume,
                                    price_adj_close = row_price_adj_close
                                    ) 

                if not created:
                    print "Didnt find date:",row_date

            else:
                count_daily_found += 1

        connection.close()
        print "Add Dailies Finished"

    def analyse_and_put_in_db(self):
        """ """                 
        #~ print row, company
        #~ row_date = datetime.strptime(str(row[0]) , '%Y-%m-%d')#'%b %d %Y %I:%M%p') #row[0],
        #~ row_price_open = float(row[1])
        #~ row_price_high = float(row[2])
        #~ row_price_low = float(row[3])
        #~ row_price_close = float(row[4])
        #~ row_price_volume = float(row[5])
        #~ row_price_adj_close = float(row[6])
        print "Start Analysis"
        price_list = []
        volume_list = []
        do_for_count = 10
        
        if self.modified:
            if self.modified.date() == datetime.now(pytz.utc).date():
                print "This record was edited today!"
                return 
                # pass

        # else:        
        for daily in self.daily_set.filter().order_by('-date'):
            #~ print daily.date
            price_list.append(calc_inflation_by_year(
                            daily.date.year,
                            daily.price_close
                            ))
            volume_list.append(daily.price_volume)

        #~ price_array = array( price_list )
        print "Dailies Loading into Arrays"

        if (
                len(price_list) > 100 and 
                len(volume_list) > 100 and
                np.average(volume_list[:100]) > MINIMUM_CURRENT_VOLUME and
                np.average(price_list[:100]) > MINIMUM_CURRENT_PRICE
                ):  
            self.has_averages = True 
       
        else:
            self.has_averages = False 
             
        self.score_undervalue = calc_score_undervalue(price_list)  
        self.price_average = np.average(price_list)    
        self.price_stdev = np.std(price_list) 
        self.price_min = np.amin(price_list) 
        self.price_max = np.amax(price_list) 
        self.price_median = np.median(price_list)
        self.modified = timezone.now()

        self.save()
        connection.close()
        print "Analysis Finished"






class Daily(models.Model):
    cid = models.ForeignKey(Company,db_index=True)
    
    date = models.DateField()
    
    price_open = models.FloatField(default=0.0)
    price_high = models.FloatField(default=0.0)
    price_low = models.FloatField(default=0.0)
    price_close = models.FloatField(default=0.0)
    price_volume = models.FloatField(default=0.0)
    price_adj_close = models.FloatField(default=0.0)
    
    
    
    
    
  
  
  
  
 
class UserProfile(models.Model):
    """ UserProfile model in a OneToOneField with User so that addl fields can be attached to Users (aka. picutre) """
    # This line is required. Links UserProfile to a User model instance.
    user = models.OneToOneField(User)

    # The additional attributes we wish to include.
    website = models.URLField(blank=True)
    picture = models.ImageField(upload_to='profile_images', blank=True)

    
    # Override the __unicode__() method to return out something meaningful!
    def __unicode__(self):
        return self.user.username
