from django.conf.urls import patterns, url, include

from ycs_apps.stock_track import views

"""Simply overrides the projects urls.py to let specific templates get filled by specific views.  """
urlpatterns = patterns('',
    # ex: /polls/
    #url(r'^$', views.index, name='index'),
    # ex: /polls/5/
    #url(r'^(?P<poll_id>\d+)/$', views.detail, name='detail'),
    # ex: /polls/5/results/
    #url(r'^(?P<poll_id>\d+)/results/$', views.results, name='results'),
    # ex: /polls/5/vote/
    #url(r'^(?P<poll_id>\d+)/vote/$', views.vote, name='vote'),


    
    url(r'^$', views.IndexView.as_view(), name='index'),
    # url(r'^new/$', views.CreateView.as_view(), name='new'),
    # url(r'^report/$', views.ReportView.as_view(), name='report'),
    url(r'^detail/(?P<pk>\w+)/$', views.DetailView.as_view(), name='detail'),
    url(r'^historical/(?P<pk>\w+)/$', views.HistoricalDetailView.as_view(), name='historical'),
    
    url(r'^lines/(?P<pk>\w+)/$', views.LinesDetailView.as_view(), name='lines'),

    url(r'^random_company/$', views.get_random_company, name='random_company'),
    url(r'^refresh_all_companies/$', views.refresh_all_companies, name='refresh_all_companies'),
    url(r'^build_new_company_dailies/$', views.build_new_company_dailies, name='build_new_company_dailies'),

    
    # url(r'^edit/(?P<slug>\w+)/$', views.UpdateView.as_view(), name='edit'),
    # url(r'^farview/(?P<slug>\w+)/$', views.FARUpdateView.as_view(), name='farview'),
    # url(r'^note/(?P<slug>\w+)/$', views.NotesUpdateView.as_view(), name='note'),
    # url(r'^pdf/(?P<slug>\w+)/$', views.pdf_maker_view, name='pdf'),
    url(r'^register/$', views.register, name='register'), # ADD NEW PATTERN!
    url(r'^login/$', views.user_login, name='login'),
    url(r'^logout/$', views.user_logout, name='logout'),


    url(r'^refresh/(?P<pk>\w+)/$', views.refresh_company_and_analyse, name='refresh'),


    url(r'^soft_new/(?P<pk>\w+)/$', views.soft_add_new_daily, name='soft_new'),
    url(r'^soft_old/(?P<pk>\w+)/$', views.soft_add_old_daily, name='soft_old'),
    url(r'^soft_analyse/(?P<pk>\w+)/$', views.soft_analyse_daily, name='soft_analyse'),


    url(r'^toggle_traded/(?P<pk>\w+)/$', views.toggle_not_traded_value, name='toggle_traded'),


    url(r'^get_ticker/(?P<pk>\w+)/$', views.get_detail_via_ticker, name='get_ticker'),

    # url(r'^userprofile/(?P<pk>\w+)/$', views.UserProfileUpdateView.as_view(), name='userprofile'),
    # url(r'^pic/(?P<pk>\w+)/$', views.NotePicUpdateView.as_view(), name='pic'),
    # url(r'^newpic/(?P<pk>\w+)/$', views.NotePicCreateView.as_view(), name='newpic'),
    # url(r'^delpic/(?P<pk>\w+)/$', views.NotePicDeleteView.as_view(), name='delpic'),
    # url(r'^delete_pic/(?P<pk>\w+)/$', views.delete_pic, name='delete_pic'),
    
    # url(r'^report_numerical/$', views.ReportNumericalView.as_view(), name='report_numerical'),
    # url(r'^report_avgtime/$', views.ReportAverageTimeView.as_view(), name='report_avgtime'),
    # url(r'^report_roundtrip/$', views.ReportRoundTripView.as_view(), name='report_roundtrip'),
    # url(r'^report_failedpartnum/$', views.ReportFailedByPartNumber.as_view(), name='report_failedpartnum')
)
