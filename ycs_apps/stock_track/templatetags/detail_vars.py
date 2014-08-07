from ycs_apps.stock_track.models import Company, Daily, UserProfile
from ycs_apps.stock_track.views import Company, Daily, UserProfile
from django import template
from random import randint
import csv
import urllib2
import StringIO

register = template.Library()


# def find_acceptable_ticker(ticker_string):
#     found_ticker = False
#     reject_string = "This is an unknown symbol."

#     site= "http://www.nasdaq.com/symbol/"+ticker_string
#     hdr = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11',
#            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
#            'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
#            'Accept-Encoding': 'none',
#            'Accept-Language': 'en-US,en;q=0.8',
#            'Connection': 'keep-alive'}

#     req = urllib2.Request(site, headers=hdr)

#     try:
#         page = urllib2.urlopen(req)
#         content = page.read()
#     except urllib2.HTTPError, e:
#         print e.fp.read()
#         content = None

#     if content:
#         if reject_string in content:
#             found_ticker = False
#             # print "Rejected "+ticker_string
#         else:
#             found_ticker = True
    
#     return found_ticker   




# def get_nasdaq_safe_rand(obj_list):
#     """ """
#     found_pk = 0
#     condition = False

#     rand_int = randint(1,obj_list.count())

#     while not condition:
#         if find_acceptable_ticker(obj_list.get(pk=rand_int).ticker):
#             condition = True
#             found_pk = rand_int


#     return found_pk

@register.simple_tag
def test(the_company):
    """ """
    
    ret_string = "   "
     
    return ret_string[1:]  #test_string#ret_string




@register.simple_tag
def goto_random_daily():
    """ """
    
    ret_string = ""
    

    # rand_pk = get_nasdaq_safe_rand(Company.objects.all())
    # rand_pk = randint(1,Company.objects.all().count())
    rand_pk = randint(1,25000)

    ret_string += "/stock_track/detail/" +str(rand_pk)+ "/"

    return ret_string  #test_string#ret_string
