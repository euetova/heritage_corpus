# coding=utf-8
u"""Управление возможными url с префиксом /RLC"""

from django.conf.urls import patterns, include, url
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from TestCorpus.views import Index, Search, Statistics, PopUp, download_file
from news.views import NewsView, SectionView
from annotator.admin import learner_admin


urlpatterns = patterns('',
                       # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),  # документация
                       url(r'^admin/', include(learner_admin.urls)),  # все страницы, связанные с панелью администратора
                       url(r'^(help|rulec)$', Index.as_view(), name='main.static'),  # страница помощи и страница рулека
                       url(r'^(search)/$', Search.as_view(), name='main.search'),  # страница поиска
                       url(r'^(news)$', NewsView.as_view(), name='news'),  # новости
                       url(r'^$', SectionView.as_view(), name='start_page'),  # стартовая
                       url(r'^search/(gramsel|lex|errsel)$', PopUp.as_view(), name='popup'),  # окна с чекбоксами
                       url(r'^(stats)/$', Statistics.as_view(), name='main.stats'),  # статистика
                       url(r'^(download_file)/(?P<doc_id>[\w\-]+)/(?P<doc_type>ann|tokens|text)$',
                           download_file, name='download_file'),
                       # скачивание текста или разметки

                       url(r'^document-annotations', include('annotator.urls')),  # все страницы, связанные с разметкой
                       (r'^i18n/', include('django.conf.urls.i18n')),  # интернационализация
                       )

urlpatterns += staticfiles_urlpatterns()