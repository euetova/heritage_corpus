# coding=utf-8
__author__ = 'elmira'

import re
import codecs
from db_utils import Database
from annotator.models import Document, Sentence, Annotation, Token, Morphology
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q

# todo make this into a neat one-line js-function
jquery = """jQuery(function ($) {$('#***').annotator().annotator('addPlugin', 'Tags').annotator('addPlugin', 'Corr').annotator('addPlugin', 'Correction', 'Enter correct variant...').annotator('addPlugin', 'ReadOnlyAnnotations').annotator('addPlugin', 'Store', {prefix: '/heritage_corpus/document-annotations',annotationData: {'document': ***},loadFromSearch: {'document': ***}});});"""
reg = re.compile(',| ')

def get_subcorpus(query):
    req = 'SELECT id FROM `annotator_document` WHERE 1 '
    if u'rulec' in query:
        req += 'AND subcorpus="RULEC" '
    mode = query.get(u'mode').encode('utf-8')
    if mode != u'any':
        req += 'AND mode="'+ mode +'" '
    background = query.get(u'background')
    if background != u'any':
        req += 'AND language_background="'+ background +'" '
    gender = query.get(u'gender').encode('utf-8')
    if gender != u'any':
        req += 'AND gender="'+ gender +'" '
    date1 = query.get(u'date1')
    if date1 != u'':
        req += 'AND date1>='+ date1 +' '
    date2 = query.get(u'date2')
    if date2 != u'':
        req += 'AND date2<='+ date2 +' '
    language = query.getlist(u'language[]')
    if language != []:
        one = []
        for lang in language:
            one.append('native="'+ lang.encode('utf-8') +'"')
        if len(one) == 1:
            req += 'AND '+ one[0] + ';'
        else:
            req += 'AND (' + ' OR '.join(one) + ')'
    db = Database()
    docs = [str(i[0]) for i in db.execute(req)]
    subsum = db.execute('SELECT SUM(sentences), SUM(words) FROM `annotator_document` WHERE id IN (' +req + ')')
    flag = False if req == 'SELECT id FROM `annotator_document` WHERE 1 ' else True
    return docs, subsum[0][0], subsum[0][1], flag

def bold(word, sent):
    s = re.sub('(\\b'+word+'\\b)', '<b>\\1</b>', sent)
    return s


def pages(sent_list, page, num):
    paginator = Paginator(sent_list, num)
    try:
        sents = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        sents = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        sents = paginator.page(paginator.num_pages)
    return sents

def exact_search(word, docs, flag):
    db = Database()
    # db.cur.execute('SELECT tok.sent_id, tok.doc_id, sent.text FROM `annotator_token` tok, `annotator_sentence` sent WHERE tok.token="дом" and tok.sent_id=sent.id;')
    req1 = 'SELECT COUNT(DISTINCT doc_id) FROM `annotator_token` WHERE token="'+word + '" '
    if flag:
        req1 += 'AND doc_id IN ('+','.join(docs) + ');'
    docs_len = int(db.execute(req1)[0][0])
    req2 = 'SELECT DISTINCT sent_id FROM `annotator_token` WHERE token="'+ word +'" '
    if flag:
        req2 += 'AND doc_id IN ('+','.join(docs) + ');'
    tokens = db.execute(req2)
    # tokens = Token.objects.filter(token__exact=word)
    jq = []
    sent_list = [Sentence.objects.get(pk=token[0]) for token in tokens]
    for sent in tokens:
        # sent.temp = bold(word, sent.tagged)
        # sent.save()
        jq.append(jquery.replace('***', str(sent[0])))
    return jq, sent_list, word, docs_len

def lex_search(query, docs, flag):
    # print query
    words = query.getlist(u'wordform[]')
    lexis = query.getlist(u'lex[]')
    grams = query.getlist(u'grammar[]')
    errs = query.getlist(u'errors[]')
    # print query.getlist(u'major'), query.getlist(u'genre')
    # froms = query.getlist(u'from[]')
    # tos = query.getlist(u'to[]')
    # <QueryDict: u'wordform[]' u'date1':  u'grammar[]': [u'S', u'A'], [u''], u'format': [u'full'], u'errors[]': u'from[]' u'major':  u'sort_by': [u'wordform'], u'additional[]': u'gender' u'genre'  u'per_page': [u'10'], u'expand': [u'+-1'], u'to[]'}>
    sent_list = {}
    jq = []
    # for wn in xrange(len(words)):
    wn = 0
    word = words[wn].lower().encode('utf-8')
    lex = lexis[wn].encode('utf-8')
    gram = grams[wn].encode('utf-8')
    err = errs[wn].encode('utf-8')
    rows = collect_data([word, lex, gram, err, docs, flag])
    sent_list = [Sentence.objects.get(pk=row[0]) for row in rows]
    for sent in rows:
        jq.append(jquery.replace('***', str(sent[0])))
    word=' '.join(query.getlist(u'wordform[]'))
    return jq, sent_list, word, len(set([s.doc_id for s in sent_list]))


def collect_data(arr):
    word, lex, gram, err, docs, flag = arr
    if [word, lex, gram] == ["", "", ""] and err != '':
        req = 'SELECT document_id FROM annotator_annotation WHERE 1 '
        errs = [i for i in reg.split(err.lower()) if i != '']
        for er in errs:
            req += 'AND tag LIKE "%' + er + '%" '
    else:
        if err != '':
            req = '''SELECT DISTINCT sent_id FROM  annotator_token
        LEFT JOIN annotator_morphology
        ON annotator_token.id = annotator_morphology.token_id
        LEFT JOIN annotator_annotation
        ON annotator_token.sent_id = annotator_annotation.document_id
        WHERE 1 '''
            errs = [i for i in reg.split(err.lower()) if i != '']
            for er in errs:
                req += 'AND tag LIKE "%' + er + '%" '
            req += 'AND num>= annotator_annotation.start AND num <= annotator_annotation.end '
        else:
            req = '''SELECT DISTINCT sent_id FROM  annotator_token
        LEFT JOIN annotator_morphology
        ON annotator_token.id = annotator_morphology.token_id
        WHERE 1 '''
        if word != '':
            req += 'AND lem="'+word+'" '
        if lex != '':
            req += 'AND lex LIKE "%' + lex + '%" '
        if gram != '':
            grams = [i for i in reg.split(gram) if i != '']
            for gr in grams:
                req += 'AND gram LIKE "%' + gr + '%" '
    if flag:
        req += 'AND doc_id IN ('+','.join(docs)+');'
    # f = codecs.open('s.txt', 'w')
    # f.write(req)
    # f.close()
    db = Database()
    rows = db.execute(req)
    return rows