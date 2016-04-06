# -*- coding=utf-8 -*-
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response, redirect, render
#from models import Doc, Sentence, Error, Analysis, Token
from annotator.models import Document, Sentence, Annotation, Token, Morphology
from django.views.generic.base import View
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.exceptions import PermissionDenied, ObjectDoesNotExist
from django.http import HttpResponse, HttpResponseServerError, HttpResponseBadRequest, HttpResponseNotFound, HttpResponseForbidden
from django.views.generic import View
from django.views.generic.base import TemplateView
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import permission_required
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.template import *
from search import *
from collections import Counter
from itertools import chain
from db_utils import Database
import re
import HTMLParser
h = HTMLParser.HTMLParser()
rePage = re.compile(u'&page=\\d+', flags=re.U)
import json


def download_file(request, doc_id, doc_type):
    db = Database()
    if doc_type == 'ann':
        req = "SELECT `username`, `data`, `tag`, `start`, `end` FROM `annotator_annotation` LEFT JOIN `auth_user` ON annotator_annotation.owner_id=auth_user.id WHERE `document_id` in (SELECT id FROM `annotator_sentence` WHERE `doc_id_id`=%s)" %doc_id
        text = u'Разметчик\tОшибка\tИсправление\tТэг\tНачало ошибки (номер слова от начала предложения)\tКонец ошибки (номер слова от начала предложения)\r\n'
        rows = db.execute(req)
        for row in rows:
            data = json.loads(row[1])
            text += '\t'.join([str(row[0]), data['quote'], data['corrs'], row[2], str(row[3]), str(row[4])]) + '\r\n'
        response = HttpResponse(text, content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="annotation_text_%s.csv"' %doc_id
        return response
    elif doc_type == u'text':
        req = "SELECT text FROM `annotator_sentence` WHERE `doc_id_id`=%s" %doc_id
        text = ' '.join(h.unescape(i[0]).encode('cp1251') for i in db.execute(req))
        response = HttpResponse(text, content_type='text/plain')
        response['Content-Disposition'] = 'filename="text_%s.txt"' %doc_id
        return response
    else:
        req = "SELECT `token`,`num`, `sent_id` FROM `annotator_token` WHERE `doc_id`=%s" %doc_id
        rows = u'Номер предложения в базе данных\tСлово\tНомер слова в предложении\tТэги\tИсправление\tРазметчик\r\n' + u'\r\n'.join(u'\t'.join([str(row[2]),row[0], str(row[1]), '', '', '']) for row in db.execute(req))
        response = HttpResponse(rows, content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="tokens_text_%s.txt"' %doc_id
        return response


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
            # QueryFormset = formset_factory(QueryForm, extra=2)
            return render_to_response('search.html',
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
            page = request.GET.get('page')
            page = int(page) if page else 1
            expand = int(query.get(u'expand')[-1])
            if "exact_search" in query:
                jq, sent_list, word, res_docs, res_num = exact_full_search(request.GET["exact_word"].lower().encode('utf-8'), subcorpus, flag, expand, page, per_page)

            else:
                # todo rewrite this part of search
                jq, sent_list, word, res_docs, res_num = lex_search(query, subcorpus, flag, expand, page, per_page)


            paginator = Paginator(['']*res_num, per_page)
            start = page - 10 if page > 10 else 1
            end = page + 10 if page + 10 <= paginator.num_pages else paginator.num_pages
            paginator.page_range2 = range(start, end+1)
            try:
                sents = paginator.page(page)
            except PageNotAnInteger:
                # If page is not an integer, deliver first page.
                sents = paginator.page(1)
            except EmptyPage:
                # If page is out of range (e.g. 9999), deliver last page of results.
                sents = paginator.page(paginator.num_pages)
            full_path = rePage.sub('', request.get_full_path())
            return render_to_response('result.html',
                                      {'query': word, 'result': sent_list, 'pages': sents,
                                       'numbers': count_data,
                                       'total': res_num, 'total_docs': res_docs,
                                       'path':full_path, 'j':jq, 'olstart': (page-1)*per_page + 1},
                                      context_instance=RequestContext(request))


class Statistics(Index):
    def merge_two_dicts(self, x, y):
        '''Given two dicts, merge them into a new dict as a shallow copy.'''
        z = x.copy()
        z.update(y)
        return z

    def get(self, request, page):
        docs =Document.objects.all().count()
        doc_ann = Document.objects.filter(annotated=True).count()
        doc_ann_percent = int(100*float(doc_ann)/docs)
        doc_check = Document.objects.filter(checked=True).count()
        doc_check_percent = int(100*float(doc_check)/docs)
        sents = Sentence.objects.all().count()
        words = Token.objects.all().count()
        annotations = Annotation.objects.all().count()
        a = defaultdict(str)
        repl = lambda i, j: self.merge_two_dicts(a, dict(j))[i]
        gender = dict(Counter([repl(i.gender, Document.GenderChoices) for i in Document.objects.all()]))
        genres = dict(Counter([i.genre for i in Document.objects.all()]))
        lb = dict(Counter([repl(i.language_background, Document.BackgroundChoices) for i in Document.objects.all()]))
        native = dict(Counter([repl(i.native, Document.NativeChoices) for i in Document.objects.all()]))

        return render_to_response('stats.html', {'docs':docs,
                                                 'progress': [doc_ann, doc_ann_percent,
                                                              doc_check, doc_check_percent],
                                                 'sents':sents,
                                                 'words':words,
                                                 'annot':annotations,
                                                 'gender':gender,
                                                 'genres':genres,
                                                 'lb': lb,
                                                 'native': native,
                                                 # 'request':request
        },
                                  context_instance=RequestContext(request))
# todo write login \ registration (if needed??)