from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.conf.urls.i18n import i18n_patterns
from django.utils.translation import ugettext_lazy as _
from TestCorpus.views import Index, Search, Statistics, PopUp, download_file
from news.views import NewsView, SectionView
from annotator.admin import learner_admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns


urlpatterns = patterns('',
    url(r'^admin/', include(learner_admin.urls)),
    url(r'^(help|rulec)$', Index.as_view(), name='main.static'),
    url(r'^(search)/$', Search.as_view(), name='main.search'),
    url(r'^(news)$', NewsView.as_view(), name='news'),
    url(r'^$', SectionView.as_view(), name='start_page'),
    url(r'^search/(gramsel|lex|errsel)$', PopUp.as_view(), name='popup'),
    url(r'^(stats)/$', Statistics.as_view(), name='main.stats'),
    url(r'^(download_file)/(?P<doc_id>[\w\-]+)/(?P<doc_type>ann|tokens|text)$', download_file, name='download_file'),
    url(r'^document-annotations', include('annotator.urls')),
    (r'^i18n/', include('django.conf.urls.i18n')),
    )
# urlpatterns += i18n_patterns('',
#     url(r'^(stats)/$', Statistics.as_view(), name='main.stats'),
# )

urlpatterns += staticfiles_urlpatterns()