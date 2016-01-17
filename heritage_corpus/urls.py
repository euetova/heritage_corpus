from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.conf.urls.i18n import i18n_patterns
from django.utils.translation import ugettext_lazy as _
from TestCorpus.views import Index, Search, Statistics, PopUp, download_file
from news.views import NewsView, SectionView
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
    url(r'^(index2|help|start|publications|authors|texts|annotation|team|rulec)$', Index.as_view(), name='main.static'),
    url(r'^(search)/$', Search.as_view(), name='main.search'),
    url(r'^(news)$', NewsView.as_view(), name='news'),
    url(r'^$', SectionView.as_view(), name='start_page'),
    url(r'^search/(gramsel|lex|errsel)$', PopUp.as_view(), name='popup'),
    url(r'^(stats)/$', Statistics.as_view(), name='main.stats'),
    url(r'^(download_file)/(?P<doc_id>[\w\-]+)/(?P<doc_type>ann|tokens|text)$', download_file, name='download_file'),
    url(r'^document-annotations', include('annotator.urls')),
    url(dajaxice_config.dajaxice_url, include('dajaxice.urls')),
    (r'^i18n/', include('django.conf.urls.i18n')),
    )
# urlpatterns += i18n_patterns('',
#     url(r'^(stats)/$', Statistics.as_view(), name='main.stats'),
# )

urlpatterns += staticfiles_urlpatterns()