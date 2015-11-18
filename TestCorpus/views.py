# -*- coding=utf-8 -*-
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response, redirect, render
#from models import Doc, Sentence, Error, Analysis, Token
from annotator.models import Document, Sentence, Annotation, Token, Morphology
from django.views.generic.base import View
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from forms import QueryForm
from django.core.exceptions import PermissionDenied, ObjectDoesNotExist
from django.http import HttpResponse, HttpResponseServerError, HttpResponseBadRequest, HttpResponseNotFound, HttpResponseForbidden
from django.views.generic import View
from django.views.generic.base import TemplateView
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import permission_required
from django.conf import settings
from django.template import *
from search import *
from collections import Counter
from itertools import chain

import re
rePage = re.compile(u'&page=\\d+', flags=re.U)

from django.forms.formsets import formset_factory


class Struct:
    def __init__(self, **values):
        vars(self).update(values)


class Index(View):

    def get(self, request, page):
        doc_list = Document.objects.all()
        # эта функция просто достает нужный шаблон и показывает его
        if page == '':
            return render_to_response(u'start.html', {'docs': doc_list}, context_instance=RequestContext(request))
        page = 'simple/' + page + '.html'
        return render_to_response(page, {'docs': doc_list}, context_instance=RequestContext(request))

class PopUp(View):

    def get(self, request, page):
        page = 'search/' + page + '.html'
        return render_to_response(page, context_instance=RequestContext(request))


class Search(Index):
    # тут все для поиска

    # todo write search
    def get(self, request, page):  # page does nothing here, just ignore it
        if len(request.GET) < 1:
            QueryFormset = formset_factory(QueryForm, extra=2)
            return render_to_response('search.html', {'form': QueryFormset},
                                      context_instance=RequestContext(request))
        else:
            # print request.GET
            query = request.GET
            subcorpus, subcorpus_sents, subcorpus_words, flag = get_subcorpus(query)
            # print subcorpus.count()
            # subcorpus_sents = [sent.id for doc in subcorpus[0] for sent in doc.sentence_set.all()]
            count_data = {'total_docs': Document.objects.count(),
                          'total_sents': Sentence.objects.count(),
                          'total_tokens': Token.objects.count(),
                          'subcorpus_docs': len(subcorpus),
                          'subcorpus_sents': subcorpus_sents,
                          'subcorpus_words': subcorpus_words}
            per_page = int(query.get(u'per_page'))
            if query["exact_word"] != '':
                jq, sent_list, word, res_docs = exact_search(request.GET["exact_word"].lower().encode('utf-8'), subcorpus, flag)

            else:
                # QueryFormset = formset_factory(QueryForm)
                # formset = QueryFormset(request.GET, request.FILES)
                # if formset.is_valid():
                # todo rewrite this part of search
                jq, sent_list, word, res_docs = lex_search(query, subcorpus, flag)

            page = request.GET.get('page')
            sents = pages(sent_list, page, per_page)
            # if page:
            #     start = page - 10 if page - 10 > 0 else 1
            #     end = page + 10 if page + 10 <= sents.paginator.num_pages else sents.paginator.num_pages
            # else:
            #     start = 1
            #     end = 11
            # sents.paginator.page_range = range(start, end)
            full_path = rePage.sub('', request.get_full_path())
            return render_to_response('result.html',
                                      {'query': word, 'result': sents,
                                       'numbers': count_data,
                                       'total': len(sent_list), 'total_docs': res_docs,
                                       'path':full_path, 'j':jq},
                                      context_instance=RequestContext(request))


class Statistics(Index):

    def get(self, request, page):
        docs =Document.objects.all().count()
        doc_ann = Document.objects.filter(annotated=True).count()
        doc_ann_percent = int(100*float(doc_ann)/docs)
        doc_check = Document.objects.filter(checked=True).count()
        doc_check_percent = int(100*float(doc_check)/docs)
        sents = Sentence.objects.all().count()
        words = Token.objects.all().count()
        annotations = Annotation.objects.all().count()
        gender = dict(Counter([i.gender for i in Document.objects.all()]))
        genres = dict(Counter([i.genre for i in Document.objects.all()]))
        lb = dict(Counter([i.language_background for i in Document.objects.all()]))
        native = dict(Counter([i.native for i in Document.objects.all()]))

        return render_to_response('stats.html', {'docs':docs,
                                                 'progress': [doc_ann, doc_ann_percent,
                                                              doc_check, doc_check_percent],
                                                 'sents':sents,
                                                 'words':words,
                                                 'annot':annotations,
                                                 'gender':gender,
                                                 'genres':genres,
                                                 'lb': lb,
                                                 'native': native},
                                  context_instance=RequestContext(request))
# todo write login \ registration (if needed??)