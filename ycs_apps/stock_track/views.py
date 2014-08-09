from django.shortcuts import render, get_object_or_404, render_to_response
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.template import RequestContext, loader
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.forms.util import ErrorList

from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout

from ycs_apps.stock_track.models import Company, Daily, UserProfile
from django.contrib.auth.models import User
from django.views import generic
from django.utils import timezone

from ycs_apps.stock_track.forms import *
from django.db.models import Q

from django.db import connection

from django.utils import timezone
from datetime import *
import _strptime
import pytz

import csv
import urllib2
import StringIO

import numpy as np
from random import randint
# Create your views here.



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
        company.price_
        company.score_undervalue = calc_score_undervalue(price_list)
        company.has_averages = True 
   
    else:
        company.score_undervalue = calc_score_undervalue(price_list)  
        company.has_averages = False 
         

    company.price_average = np.average(price_list)    
    company.price_stdev = np.std(price_list) 
    company.price_min = np.amin(price_list) 
    company.price_max = np.amax(price_list) 
    company.price_median = np.median(price_list)
    company.modified = timezone.now()

    company.save()
    connection.close()


def add_dailies_to_company(the_company, only_try=None,try_old_only=False):
    """ """

    now_ish = datetime.today()
    future_year = now_ish.year+1
    past_year = now_ish.year-70

    the_url_string ="http://real-chart.finance.yahoo.com/table.csv?s="
    the_url_string += str(the_company.ticker)+"&a=11&b=31&c="
    the_url_string += str(past_year)+"&d=00&e=1&f="
    the_url_string += str(future_year)+"&g=d&ignore=.csv"
    


    print "Get CSV"
    try:
        csv_url_opened = urllib2.urlopen(the_url_string)
        cr = csv.reader(csv_url_opened)
        the_company.activated = True
        the_company.save()
    except:
        the_company.activated = False
        the_company.save()
        return response
        
    count = 0
    count_actually_inserted = 0
    count_daily_found = 0
    centi_count = 0

    print "Daily"
    daily_queryset = Daily.objects.filter(cid=the_company.id)

    for row in cr:
        count += 1

        if count == 1:
            continue

        if count % 1000 == 0:
            centi_count += 1
            print str(centi_count*1000)+" Entries reviewed!"   

        if only_try:
            if count_actually_inserted > only_try:
                break #we we insert only_try, no mater what break

            if not try_old_only:
                if count_daily_found > only_try:
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
                                cid_id = the_company.id,
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


def find_acceptable_pk(obj_list):
    """ """

    found_pk = 0
    condition = False
    reject_string = "This is an unknown symbol."

    total_objs = obj_list.count()

    while not condition:
        rand_int = randint(1,total_objs)
        the_company = obj_list.get(pk=rand_int)
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













                                  
class IndexView(generic.ListView):
    """ Class-based-view for listing stock_track entries  """
    template_name = 'stock_track/index.html'
    # context_object_name = 'latest_rma_list'

    def get_queryset(self):
#        """Return the last five published polls."""
#        return Poll.objects.order_by('-pub_date')[:5]
        """
        Return the QuerySet of all RMA objects in a particular order
        """
        #return RMA.objects.order_by('-date_created')
        # return RMA.objects.exclude(Metatag.objects.filter(text="AUTOCREATED")).order_by('-date_created')
        # # banned_song_ids = (BannedSong.objects.filter(lib_entry__player=activePlayer)
                        # # .values_list('lib_entry', flat=True))

        # # available_songs = (LibraryEntry.objects.filter(player=activePlayer)
                        # # .exclude('id__in' = banned_song_ids))
        #unwanted_tags = Metatag.objects.filter(text="INDEX_HIDDEN").values_list('rma', flat=True)
        #valid_rma_entries = RMA.objects.all().exclude(id__in = unwanted_tags)
        #return valid_rma_entries.order_by('-date_created')
        return Company.objects.filter(
                                activated=True,
                                has_averages=True,
                                score_undervalue__gte=1 #ensure at least an 'ok' score
                                ).order_by('ticker')
####################





class DetailView(generic.DetailView):
    """ Class-based-view for showing fields of a specific SATURN entry  """
    model = Company
    template_name = 'stock_track/detail.html'
    #~ slug_field = 'ro_num'
    #slug_url_kwarg = 'rm_num'
    #context_object_name = 'rma_detail'
    # def test_value(self):
        # return model.rm_num
    #test_value = get_context_data().rm_num
    #slug_url_kwarg = 'rm_num'
    # def get_object(self):
        # return get_object_or_404(RMA, pk=RMA.rm_num)
    
    #context_object_name = 'rma_detail_list'
    
    #~ def get_queryset(self):
        #~ qs = super(DetailView, self).get_queryset()
        #~ return qs.order_by('-date')
        
        
    def get_context_data(self, **kwargs):
        """ Allows changes to context data for templates """

        context = super(DetailView, self).get_context_data(**kwargs)
        context['display_type']="Detail"
        return context






class HistoricalDetailView(generic.DetailView):
    """ Class-based-view for showing fields of a specific SATURN entry  """
    model = Company
    template_name = 'stock_track/historical.html'
        
    def get_context_data(self, **kwargs):
        """ Allows changes to context data for templates """
        context = super(HistoricalDetailView, self).get_context_data(**kwargs)
        context['display_type']="Historical"
        return context
        
        
        
        

class LinesDetailView(generic.DetailView):
    """ Class-based-view for showing fields of a specific SATURN entry  """
    model = Company
    template_name = 'stock_track/lines.html'


    def get_context_data(self, **kwargs):
        """ Allows changes to context data for templates """

        context = super(LinesDetailView, self).get_context_data(**kwargs)
        context['display_type']="Lines"
        return context
        
        
        

  
def register(request):
    """
    Non-Class-based view for registering new users
    """
    # Like before, get the request's context.
    context = RequestContext(request)
    context['display_type']="Register"
    # A boolean value for telling the template whether the registration was successful.
    # Set to False initially. Code changes value to True when registration succeeds.
    registered = False

    # If it's a HTTP POST, we're interested in processing form data.
    if request.method == 'POST':
        # Attempt to grab information from the raw form information.
        # Note that we make use of both UserForm and UserProfileForm.
        user_form = UserForm(data=request.POST)
        profile_form = UserProfileForm(data=request.POST)

        # If the two forms are valid...
        if user_form.is_valid() and profile_form.is_valid():
            # Save the user's form data to the database.
            user_is_unique = False
            try:
                username = User.objects.get(username=user_form.cleaned_data['username'])
            except ObjectDoesNotExist:
                user_is_unique = True
                
            if user_is_unique   : 
                user = user_form.save()
                #user = user_form.save()
                user.is_active = False
                # Now we hash the password with the set_password method.
                # Once hashed, we can update the user object.
                user.set_password(user.password)
                user.save()

                # Now sort out the UserProfile instance.
                # Since we need to set the user attribute ourselves, we set commit=False.
                # This delays saving the model until we're ready to avoid integrity problems.
                profile = profile_form.save(commit=False)
                profile.user = user

                # Did the user provide a profile picture?
                # If so, we need to get it from the input form and put it in the UserProfile model.
                if 'picture' in request.FILES:
                    profile.picture = request.FILES['picture']

                # Now we save the UserProfile model instance.
                profile.save()

                # Update our variable to tell the template registration was successful.
                registered = True
            else:
                user_form._errors["username"] = ErrorList([u"User with that name already exists!"])
                
        # Invalid form or forms - mistakes or something else?
        # Print problems to the terminal.
        # They'll also be shown to the user.
        else:
            print user_form.errors, profile_form.errors

    # Not a HTTP POST, so we render our form using two ModelForm instances.
    # These forms will be blank, ready for user input.
    else:
        user_form = UserForm()
        profile_form = UserProfileForm()

    # Render the template depending on the context.
    return render_to_response(
            'stock_track/register.html',
            {'user_form': user_form, 'profile_form': profile_form, 'registered': registered},
            context)
            
            
            
            
            
def user_login(request):
    """
    Non-Class-based view for User log in
    """
    # Like before, obtain the context for the user's request.
    context = RequestContext(request)
    context['display_type']="Login"
    
    
    # If the request is a HTTP POST, try to pull out the relevant information.
    if request.method == 'POST':
        # Gather the username and password provided by the user.
        # This information is obtained from the login form.
        username = request.POST['username']
        password = request.POST['password']

        # Use Django's machinery to attempt to see if the username/password
        # combination is valid - a User object is returned if it is.
        user = authenticate(username=username, password=password)

        # If we have a User object, the details are correct.
        # If None (Python's way of representing the absence of a value), no user
        # with matching credentials was found.
        if user:
            # Is the account active? It could have been disabled.
            if user.is_active:
                # If the account is valid and active, we can log the user in.
                # We'll send the user back to the homepage.
                login(request, user)
                return HttpResponseRedirect('/stock_track/')
            else:
                # An inactive account was used - no logging in!
                response_text = "<h1><a href='/stock_track'>Your stock_track account is not enabled. </a></h1>"
                response_text += "<BR> Please contact the stock_track administrator."
                return HttpResponse(response_text)
        else:
            # Bad login details were provided. So we can't log the user in.
            print "Invalid login details: {0}, {1}".format(username, password)
            return HttpResponse("<a href='/stock_track'>Invalid login details supplied for "+username+".</a>")

    # The request is not a HTTP POST, so display the login form.
    # This scenario would most likely be a HTTP GET.
    else:
        # No context variables to pass to the template system, hence the
        # blank dictionary object...
        if request.user.is_authenticated():
            return HttpResponseRedirect('/stock_track/')
        return render_to_response('stock_track/login.html', {}, context)



# Use the login_required() decorator to ensure only those logged in can access the view.
@login_required
def user_logout(request):
    """
    Non-Class-based view for User log out
    """
    # Since we know the user is logged in, we can now just log them out. ###
    logout(request)

    # Take the user back to the homepage.
    return HttpResponseRedirect('/stock_track/')




@login_required
def refresh_company_and_analyse(request,pk):
    """ """
    the_company = Company.objects.get(pk=pk)

    response = HttpResponseRedirect('/stock_track/detail/'+pk+'/')

    add_dailies_to_company(the_company)
        

        #         ) 
    print "Analysis"
    analyse_and_put_in_db(the_company)
    connection.close()  

    return response

    # response = render_to_response('stock_track/index.html', {}, context_instance=RequestContext(request))
    # return response
    # return HttpResponseRedirect('/stock_track/')
    # return render_to_response('stock_track/')

# reverse('detail',kwargs={'pk': pk})
# return reverse('detail',kwargs={'slug': self.get_object().ro_num})
    # return HttpResponseRedirect(reverse('detail',kwargs={'pk': pk}))


# def delete_pic(request,pk):
#    #+some code to check if New belongs to logged in user
#    note = NotePic.objects.get(pk=pk).rma.ro_num
#    u = NotePic.objects.get(pk=pk).delete()     ###
#    return HttpResponseRedirect('/SATURN/detail/'+note+'/')

@login_required
def get_detail_via_ticker(request,pk):
    """ """
    the_ticker = str(pk)
    the_company = Company.objects.get(ticker=the_ticker)

    response = HttpResponseRedirect('/stock_track/detail/'+str(the_company.pk)+'/')

    return response




@login_required
def soft_add_new_daily(request,pk):
    """ """
    # the_ticker = str(pk)
    # the_company = Company.objects.get(ticker=the_ticker)
    the_company = Company.objects.get(pk=pk)

    response = HttpResponseRedirect('/stock_track/detail/'+str(pk)+'/')

    add_dailies_to_company(the_company, only_try=50)

    return response

@login_required
def soft_add_old_daily(request,pk):
    """ """
    # the_ticker = str(pk)
    # the_company = Company.objects.get(ticker=the_ticker)
    the_company = Company.objects.get(pk=pk)

    response = HttpResponseRedirect('/stock_track/detail/'+str(pk)+'/')

    add_dailies_to_company(the_company, only_try=50,try_old_only=True)

    return response

@login_required
def soft_analyse_daily(request,pk):
    """ """
    # the_ticker = str(pk)
    the_company = Company.objects.get(pk=pk)

    response = HttpResponseRedirect('/stock_track/detail/'+str(pk)+'/')

    print "Analysis"
    analyse_and_put_in_db(the_company)
    connection.close()  

    return response



@login_required
def toggle_not_traded_value(request,pk):
    """ """
    # the_ticker = str(pk)
    the_company = Company.objects.get(pk=pk)

    response = HttpResponseRedirect('/stock_track/detail/'+str(pk)+'/')

    if the_company.not_traded:
        the_company.not_traded = False
    else:
        the_company.not_traded = True

    the_company.save()

    connection.close()  

    return response



@login_required
def get_random_company(request):
    """ """
    
    obj_list = Company.objects.filter().order_by('ticker')

    found_pk = find_acceptable_pk(obj_list)


    response = HttpResponseRedirect('/stock_track/detail/'+str(found_pk)+'/')

    connection.close()  

    return response

    
