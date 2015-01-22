from django.conf.urls import patterns, include, url
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'ycs_apps.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),

    url(r'^admin/', include(admin.site.urls)),
    
    url(r'^(?i)stock_track/', include('ycs_apps.stock_track.urls', namespace="stock_track")),
    url(r'^(?i)stock_track/', include('ycs_apps.stock_track.urls')),
    url(r'^(?i)/', include('ycs_apps.stock_track.urls', namespace="stock_track")),
    url(r'^(?i)/', include('ycs_apps.stock_track.urls')),
    
    
)

urlpatterns += staticfiles_urlpatterns()
