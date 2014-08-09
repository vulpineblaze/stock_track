from django.db import models

from django.contrib.auth.models import User

# Create your models here.

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
