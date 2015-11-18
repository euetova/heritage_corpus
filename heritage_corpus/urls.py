from django.conf.urls import patterns, include, url
from django.contrib import admin
from TestCorpus.views import Index, Search, Statistics, PopUp
from annotator.admin import learner_admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from dajaxice.core import dajaxice_autodiscover, dajaxice_config
dajaxice_autodiscover()


urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'learner_corpus.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),
    # url(r'^myadmin/', include(learner_admin.urls)),

    url(r'^admin/', include(learner_admin.urls)),
    url(r'^(|index2|help|news|start|publications|authors|texts|annotation|team|rulec)$', Index.as_view(), name='main.static'),
    url(r'^(search)/$', Search.as_view(), name='main.search'),
    url(r'^search/(gramsel|lex|errsel)$', PopUp.as_view(), name='popup'),
    url(r'^(stats)/$', Statistics.as_view(), name='main.stats'),
    url(r'^document-annotations', include('annotator.urls')),
    url(dajaxice_config.dajaxice_url, include('dajaxice.urls')),
    )

urlpatterns += staticfiles_urlpatterns()