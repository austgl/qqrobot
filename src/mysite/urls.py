from django.conf.urls import patterns, include, url
# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'mysite.views.home', name='home'),
    # url(r'^mysite/', include('mysite.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),
    url(r'^main/$','robot.views.main'),
    url(r'^main2/$','robot.views.main2'),
    url(r'^refresh/$','robot.views.refresh'),
    url(r'^letmeon/$','robot.views.main'),
    url(r'^task/$','robot.views.TASK'),
    url(r'^updateqiubai/$','mysite.mydata.Updating'),
)
