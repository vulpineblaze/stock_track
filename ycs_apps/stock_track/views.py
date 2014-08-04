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

# Create your views here.


                                  
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


