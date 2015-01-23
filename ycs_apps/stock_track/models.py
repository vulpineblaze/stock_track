from django.db import models, connection

from django.contrib.auth.models import User

from django.core.cache import cache

from datetime import *
import pytz
from django.utils import timezone

import csv
import urllib2
import StringIO

import numpy as np

from random import randint

from Queue import Queue
from threading import Thread

# from xml.dom import minidom
import urllib, cookielib

# Create your models here.


MINIMUM_CURRENT_PRICE = 5.0
MINIMUM_CURRENT_VOLUME = 10000

CPI_DICT = {}

def reset_database_connection():  
    from django import db  
    db.close_connection() 
    cache.clear() 

class Worker(Thread):
    """Thread executing tasks from a given tasks queue"""
    def __init__(self, tasks):
        Thread.__init__(self)
        self.tasks = tasks
        self.daemon = True
        self.start()

    def run(self):
        while True:
            func, args, kargs = self.tasks.get()
            try:
                func(*args, **kargs)
            except Exception, e:
                print e
            finally:
                self.tasks.task_done()

class ThreadPool:
    """Pool of threads consuming tasks from a queue"""
    def __init__(self, num_threads):
        self.tasks = Queue(num_threads)
        for _ in range(num_threads): Worker(self.tasks)

    def add_task(self, func, *args, **kargs):
        """Add a task to the queue"""
        self.tasks.put((func, args, kargs))

    def wait_completion(self):
        """Wait for completion of all the tasks in the queue"""
        self.tasks.join()

def enumerate_joiner(main_thread):
    #~ main_thread = threading.currentThread()
    for t in threading.enumerate():
        if t is main_thread:
            continue
        #~ logging.debug('joining %s', t.getName())
        try:
            t.join()
        except:
            print "error joining "+str(t.getName())
            continue

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

    def attempt_to_add_new_to_all(self, max_threads=4, quit_after_trying=0):
        """ """

        print "Request to process new dailies for "+str(quit_after_trying)+" companies has been received."
        # threads = []
        count = 0
        # recursion = 0

        start_time = datetime.now()
        reset_database_connection()

        pool = ThreadPool(max_threads)       

        # for i, d in enumerate(delays):
        #     pool.add_task(wait_delay, d)


        for company in self.iterator():
            count += 1
            # recursion += 1

        # if recursion > max_threads:
        #     recursion = 0
        #     #~ threads = thread_joiner(threads)
        #     enumerate_joiner(threading.currentThread())
                
            pool.add_task(company.add_dailies_to_company, (max_threads,quit_after_trying))   
            # threads.append(
            #     threading.Thread(
            #         name='daily_insert_'+str(count), 
            #         target=company.add_dailies_to_company,
            #         args=(max_threads,quit_after_trying)
            #         ).start()
            #     )

            if quit_after_trying and quit_after_trying > 0:
                if count >= quit_after_trying:
                    break




        pool.wait_completion()
        # enumerate_joiner(threading.currentThread())
        # connection.close()
        reset_database_connection()

        end_time = (datetime.now() - start_time)

        summary_string = "Final time was " + str(end_time.seconds//3600)+" hours, "
        summary_string += str(end_time.seconds//60%60)
        summary_string += " minutes, and " + str(end_time.seconds%60) + " seconds."
        summary_string += "\n Processed " +str(count)+"|"+str(quit_after_trying)+ " companies."
        print summary_string

        return 

    def build_new_company_dailies(self, max_threads=4, only_do_this_many=1):
        """ business logic for when running this module as the primary one!"""
        start_time = datetime.now()
        temp_time = datetime.now() - timedelta(minutes=2) #datetime.datetime.now() - datetime.timedelta(minutes=15)
        bug_in_threading_workaround_date = datetime.strptime("2014-07-30", '%Y-%m-%d')
        
        count=0
        actually_done_count = 0
        divisor = (len(self)*1.0)
        
        print "Starting processing of "+str(divisor)+" of "+str(self.count())+" companies."
        
        for company in self:
            count += 1
            actually_done = company.build_ticker_data_from_web(max_threads)
                
            if ((datetime.now() - temp_time).seconds) > 90 :
                temp_time = datetime.now()
                time_diff = temp_time - start_time
                out_string = "Accomplished "
                percent_float = "{0:.4f}".format((1.0*count/divisor)*100)
                out_string += str(percent_float)+"% with "
                out_string += str(actually_done_count)+" added in "
                out_string += str(time_diff.seconds//3600)+" hours, "
                out_string += str((time_diff.seconds//60)%60)+" minutes, and "
                out_string += str(time_diff.seconds%60)+" seconds. "
                print out_string

            if actually_done:
                actually_done_count += 1

            if (only_do_this_many and  actually_done_count > only_do_this_many):
                break

        end_time = (datetime.now() - start_time)

        summary_string = "Final time was " + str(time_diff.seconds//3600)+" hours, "
        summary_string += str(end_time.seconds//60%60)
        summary_string += " minutes, and " + str(end_time.seconds%60) + " seconds."
        if only_do_this_many:
            summary_string += "\n Stopped after "+str(only_do_this_many)+" companies had dailies added."

        left_obj_list = self.filter()
        summary_string += "\nTotal went from "+str(divisor)+" to "+str(left_obj_list.count())+" companies."
        print summary_string


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
        


        # print "Get CSV"
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

        # print "Daily"
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

        if csv_url_opened:
            csv_url_opened.close()

        connection.close()
        # print "Add Dailies Finished for "+str(self.ticker)
        return

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
        for daily in self.daily_set.filter().order_by('-date').iterator():
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

    def build_ticker_data_from_web(self, max_threads=4): # self = company
        """    """
        
        DAILIES_TO_BECOME_ACTIVE = 500 # Need ~1.5y to become active
        actually_done = False

        now_ish = datetime.today()
        future_year = now_ish.year+1

        if self.not_traded:
            return False

        if not self.find_acceptable_ticker():
            self.not_traded = True
            self.activated = False
            self.save()
            return False

        existing_dailies = Daily.objects.filter(cid=self)
        
        if self.activated:
            return False
        elif existing_dailies.count() > DAILIES_TO_BECOME_ACTIVE: 
            self.activated = True
            self.save()
            return False
        elif existing_dailies.count() > 1:
            past_year = now_ish.year-1
            #~ print "Update for "+str(self.ticker)
        else:
            past_year = now_ish.year-70
            #~ print "New Entry for "+str(self.ticker)

        
        the_url_string ="http://real-chart.finance.yahoo.com/table.csv?s="
        the_url_string += str(self.ticker)+"&a=11&b=31&c="
        the_url_string += str(past_year)+"&d=00&e=1&f="
        the_url_string += str(future_year)+"&g=d&ignore=.csv"
        

        try:
            response = urllib2.urlopen(the_url_string)
            cr = csv.reader(response)
            self.activated = True
            self.save()
        except:
            self.activated = False
            self.save()
            return False
            
        count = 0
        recursion = 0
        was_made = False
        
        #~ self.activated = True
        #~ self.save()

        pool = ThreadPool(max_threads)       

        for row in cr:
            count += 1
            recursion += 1
            
            if count == 1:
                continue

            if (count > DAILIES_TO_BECOME_ACTIVE and actually_done == False):
                actually_done = True
                self.activated = True
                self.save()
                
            pool.add_task(self.make_daily_from_row, row)  


        if response:
            response.close()

        pool.wait_completion()
        reset_database_connection()
        
        return actually_done

    def make_daily_from_row(self, row):
        """ """
        #~ print row, self
        row_date = datetime.strptime(str(row[0]) , '%Y-%m-%d')#'%b %d %Y %I:%M%p') #row[0],
        row_price_open = float(row[1])
        row_price_high = float(row[2])
        row_price_low = float(row[3])
        row_price_close = float(row[4])
        row_price_volume = float(row[5])
        row_price_adj_close = float(row[6])
        

            
        p, was_made = Daily.objects.get_or_create(
            cid_id = self.id,
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




    def find_acceptable_ticker(self):
        ticker_string = str(self.ticker)
        found_ticker = False
        reject_string = "This is an unknown symbol."

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
            print e.fp.read(), "<< Read Error"
            content = None

        if content:
            if reject_string in content:
                found_ticker = False

            else:
                found_ticker = True

        if page:
            page.close()

        return found_ticker        





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
