# coding=utf-8
__author__ = 'elmira'

import re
import codecs
from collections import defaultdict
from db_utils import Database
from annotator.models import Document, Sentence, Annotation, Token, Morphology
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q

# todo make this into a neat one-line js-function
jquery = """jQuery(function ($) {$('#***').annotator().annotator('addPlugin', 'Tags').annotator('addPlugin', 'Corr').annotator('addPlugin', 'Correction', 'Enter correct variant...').annotator('addPlugin', 'ReadOnlyAnnotations').annotator('addPlugin', 'Store', {prefix: '/heritage_corpus/document-annotations',annotationData: {'document': ***},loadFromSearch: {'document': ***}});});"""
reg = re.compile(',| ')
regToken= re.compile('">(.*?)</span>', flags=re.U | re.DOTALL)
regSpans = re.compile('[.?,!:«(;#№–/...)»-]*<span .*?</span>[.?,!:«(;#№–/...)»-]*', flags=re.U | re.DOTALL)


class ShowSentence:
    def __init__(self, sent_id, num, expand):
        k = Sentence.objects.get(pk=sent_id)
        self.tagged = self.bold(k.tagged, num)
        self.id = sent_id
        self.doc_id = k.doc_id
        self.correct = k.correct
        self.expand = ''
        for i in range(sent_id-expand, sent_id):
            try:
                sent = Sentence.objects.get(pk=i)
                self.expand += sent.tagged + ' '
            except:
                pass
        self.expand += self.tagged + ' '
        for i in range(sent_id+1, sent_id+expand+1):
            try:
                sent = Sentence.objects.get(pk=i)
                self.expand += sent.tagged + ' '
            except:
                pass

    def bold(self, tagged, num):
        s = regSpans.findall(tagged)
        for i in num:
            try:
                s[i-1] = regToken.sub('"><b>\\1</b></span>', s[i-1])
            except:
                pass  #todo find the bug here
                # with codecs.open('s.txt', 'w', encoding='utf-8') as f:
                #     f.write(' '.join(str(ciph) for ciph in num))
                #     f.write('\r\n')
                #     f.write(tagged)
        return ' '.join(s)


def get_subcorpus(query):
    req = 'SELECT id FROM `annotator_document` WHERE 1 '
    if u'rulec' in query:
        req += 'AND subcorpus="RULEC" '
    mode = query.get(u'mode').encode('utf-8')
    if mode != u'any':
        req += 'AND mode="'+ mode +'" '
    background = query.get(u'background').encode('utf-8')
    if background != u'any':
        req += 'AND language_background="'+ background +'" '
    gender = query.get(u'gender').encode('utf-8')
    if gender != u'any':
        req += 'AND gender="'+ gender +'" '
    date1 = query.get(u'date1')
    if date1 != u'':
        req += 'AND date1>='+ date1.encode('utf-8') +' '
    date2 = query.get(u'date2')
    if date2 != u'':
        req += 'AND date2<='+ date2.encode('utf-8') +' '
    language = query.getlist(u'language[]')
    if language != []:
        one = []
        for lang in language:
            one.append('native="'+ lang.encode('utf-8') +'"')
        if len(one) == 1:
            req += 'AND '+ one[0]
        else:
            req += 'AND (' + ' OR '.join(one) + ')'
    # with codecs.open('s.txt', 'w', encoding='utf-8') as f:
    #     f.write(req)
    db = Database()
    docs = [str(i[0]) for i in db.execute(req)]
    subsum = db.execute('SELECT SUM(sentences), SUM(words) FROM `annotator_document` WHERE id IN (' +req + ')')
    flag = False if req == 'SELECT id FROM `annotator_document` WHERE 1 ' else True
    return docs, subsum[0][0], subsum[0][1], flag


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


def exact_search(word, docs, flag, expand, page, per_page):
    db = Database()
    # db.cur.execute('SELECT tok.sent_id, tok.doc_id, sent.text FROM `annotator_token` tok, `annotator_sentence` sent WHERE tok.token="дом" and tok.sent_id=sent.id;')
    req1 = 'SELECT COUNT(DISTINCT doc_id) FROM `annotator_token` WHERE token="'+word + '" '
    if flag:
        req1 += 'AND doc_id IN ('+','.join(docs) + ');'
    docs_len = int(db.execute(req1)[0][0])
    n_req = 'SELECT COUNT(DISTINCT sent_id) FROM `annotator_token` WHERE token="'+ word +'" '
    if flag:
        n_req += 'AND doc_id IN ('+','.join(docs) + ');'
    sent_num = int(db.execute(n_req)[0][0])
    req2 = 'SELECT DISTINCT sent_id FROM `annotator_token` WHERE token="'+ word +'" '
    if flag:
        req2 += 'AND doc_id IN ('+','.join(docs) + ')'
    req2 += ' LIMIT %d,%d;' %((page - 1)*per_page, per_page)
    sentences = '(' + ', '.join([str(i[0]) for i in db.execute(req2)]) + ')'
    req3 = 'SELECT sent_id, num FROM `annotator_token` WHERE token="'+ word +'" AND sent_id IN ' + sentences
    tokens = db.execute(req3)
    # tokens = Token.objects.filter(token__exact=word)
    e = defaultdict(list)
    for i, j in tokens:
        e[i].append(j)
    jq = []
    sent_list = [ShowSentence(i, e[i], expand) for i in e]
    for sent in sent_list:
        # sent.temp = bold(word, sent.tagged)
        # sent.save()
        jq.append(jquery.replace('***', str(sent.id)))
    return jq, sent_list, word, docs_len, sent_num

def lex_search(query, docs, flag, expand, page, per_page):
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
    rows, sent_num, d_num = collect_data([word, lex, gram, err, docs, flag, page, per_page])
    e = defaultdict(list)
    if rows:
        if len(rows[0]) == 2:
            for i, j in rows:
                e[i].append(j)
        else:
            for i, j, k in rows:
                for n in range(j, k+1):
                    e[i].append(n)
    sent_list = [ShowSentence(i, e[i], expand) for i in e]
    for sent in sent_list:
        jq.append(jquery.replace('***', str(sent.id)))
    word=' '.join(query.getlist(u'wordform[]'))
    return jq, sent_list, ' '.join([word, lex, gram, err]), d_num, sent_num


def collect_data(arr):
    db = Database()
    word, lex, gram, err, docs, flag, page, per_page = arr
    err = err.strip()
    s = bincode(word, lex, gram, err)
    if s == '0000':
        return []
    elif s == '0001':
        req_template = ''' FROM annotator_annotation
                 LEFT JOIN annotator_sentence
                 ON annotator_annotation.document_id = annotator_sentence.id WHERE 1 '''
        req_template += parse_gram(err, 'tag')
        if flag:
            req_template += 'AND doc_id_id IN ('+','.join(docs)+')'
        n_req = '''SELECT COUNT(DISTINCT document_id)''' + req_template
        req1 = 'SELECT DISTINCT document_id' + req_template
        req = 'SELECT DISTINCT document_id, start, end' + req_template
        d_req = '''SELECT COUNT(DISTINCT doc_id_id)''' + req_template
    elif s == '0010':
        req_template = ''' FROM  annotator_morphology
        LEFT JOIN annotator_token
        ON annotator_token.id = annotator_morphology.token_id
        WHERE 1 '''+ parse_gram(gram, 'gram')
        if flag:
            req_template += 'AND doc_id IN ('+','.join(docs)+')'
        n_req = '''SELECT COUNT(DISTINCT sent_id)''' + req_template
        req1 = 'SELECT DISTINCT sent_id' + req_template
        req = 'SELECT DISTINCT sent_id, num' + req_template
        d_req = '''SELECT COUNT(DISTINCT doc_id)''' + req_template
    elif s == '0011':
        req_template = ''' FROM  annotator_token
        LEFT JOIN annotator_morphology
        ON annotator_token.id = annotator_morphology.token_id
        LEFT JOIN annotator_annotation
        ON annotator_token.sent_id = annotator_annotation.document_id
        WHERE 1 %s AND num>= annotator_annotation.start AND num <= annotator_annotation.end %s''' %(parse_gram(err, 'tag'), parse_gram(gram, 'gram'))
        if flag:
            req_template += 'AND doc_id IN ('+','.join(docs)+')'
        n_req = '''SELECT COUNT(DISTINCT sent_id)''' + req_template
        req = 'SELECT DISTINCT sent_id, num' + req_template
        req1 = 'SELECT DISTINCT sent_id' + req_template
        d_req = '''SELECT COUNT(DISTINCT doc_id)''' + req_template
    elif s == '0100':
        req_template = ''' FROM  annotator_morphology
        LEFT JOIN annotator_token
        ON annotator_token.id = annotator_morphology.token_id
        WHERE 1 '''
        req_template += parse_lex(lex)
        if flag:
            req_template += 'AND doc_id IN ('+','.join(docs)+')'
        n_req = '''SELECT COUNT(DISTINCT sent_id)''' + req_template
        req = 'SELECT DISTINCT sent_id, num' + req_template
        req1 = 'SELECT DISTINCT sent_id' + req_template
        d_req = '''SELECT COUNT(DISTINCT doc_id)''' + req_template
    elif s == '0101':
        req_template = ''' FROM  annotator_token
        LEFT JOIN annotator_morphology
        ON annotator_token.id = annotator_morphology.token_id
        LEFT JOIN annotator_annotation
        ON annotator_token.sent_id = annotator_annotation.document_id
        WHERE 1 %s AND num>= annotator_annotation.start AND num <= annotator_annotation.end %s''' %(parse_gram(err, 'tag'), parse_lex(lex))
        if flag:
            req_template += 'AND doc_id IN ('+','.join(docs)+')'
        n_req = '''SELECT COUNT(DISTINCT sent_id)''' + req_template
        req = 'SELECT DISTINCT sent_id, num' + req_template
        req1 = 'SELECT DISTINCT sent_id' + req_template
        d_req = '''SELECT COUNT(DISTINCT doc_id)''' + req_template
    elif s == '0110':
        req_template = ''' FROM  annotator_morphology
        LEFT JOIN annotator_token
        ON annotator_token.id = annotator_morphology.token_id
        WHERE 1 %s %s''' %(parse_lex(lex), parse_gram(gram, 'gram'))
        if flag:
            req_template += 'AND doc_id IN ('+','.join(docs)+')'
        n_req = '''SELECT COUNT(DISTINCT sent_id)''' + req_template
        req = 'SELECT DISTINCT sent_id, num' + req_template
        req1 = 'SELECT DISTINCT sent_id' + req_template
        d_req = '''SELECT COUNT(DISTINCT doc_id)''' + req_template
    elif s == '0111':
        req_template = ''' FROM  annotator_token
        LEFT JOIN annotator_morphology
        ON annotator_token.id = annotator_morphology.token_id
        LEFT JOIN annotator_annotation
        ON annotator_token.sent_id = annotator_annotation.document_id
        WHERE 1 %s AND num>= annotator_annotation.start AND num <= annotator_annotation.end %s %s''' %(parse_gram(err, 'tag'), parse_lex(lex), parse_gram(gram, 'gram'))
        if flag:
            req_template += 'AND doc_id IN ('+','.join(docs)+')'
        n_req = '''SELECT COUNT(DISTINCT sent_id)''' + req_template
        req = 'SELECT DISTINCT sent_id, num' + req_template
        req1 = 'SELECT DISTINCT sent_id' + req_template
        d_req = '''SELECT COUNT(DISTINCT doc_id)''' + req_template
    elif s == '1000':
        req_template = ''' FROM  annotator_morphology
        LEFT JOIN annotator_token
        ON annotator_token.id = annotator_morphology.token_id
        WHERE 1 AND lem="%s" ''' %word
        if flag:
            req_template += 'AND doc_id IN ('+','.join(docs)+')'
        n_req = '''SELECT COUNT(DISTINCT sent_id)''' + req_template
        req = 'SELECT DISTINCT sent_id, num' + req_template
        req1 = 'SELECT DISTINCT sent_id' + req_template
        d_req = '''SELECT COUNT(DISTINCT doc_id)''' + req_template
    elif s == '1001':
        req_template = ''' FROM  annotator_token
        LEFT JOIN annotator_morphology
        ON annotator_token.id = annotator_morphology.token_id
        LEFT JOIN annotator_annotation
        ON annotator_token.sent_id = annotator_annotation.document_id
        WHERE 1 AND lem="%s" AND num>= annotator_annotation.start AND num <= annotator_annotation.end %s ''' %(word,parse_gram(err, 'tag'))
        if flag:
            req_template += 'AND doc_id IN ('+','.join(docs)+')'
        n_req = '''SELECT COUNT(DISTINCT sent_id)''' + req_template
        req = 'SELECT DISTINCT sent_id, num' + req_template
        req1 = 'SELECT DISTINCT sent_id' + req_template
        d_req = '''SELECT COUNT(DISTINCT doc_id)''' + req_template
    elif s == '1010':
        req_template = ''' FROM  annotator_morphology
        LEFT JOIN annotator_token
        ON annotator_token.id = annotator_morphology.token_id
        WHERE 1 AND lem="%s" %s''' %(word, parse_gram(gram, 'gram'))
        if flag:
            req_template += 'AND doc_id IN ('+','.join(docs)+')'
        n_req = '''SELECT COUNT(DISTINCT sent_id)''' + req_template
        req = 'SELECT DISTINCT sent_id, num' + req_template
        req1 = 'SELECT DISTINCT sent_id' + req_template
        d_req = '''SELECT COUNT(DISTINCT doc_id)''' + req_template
    elif s == '1011':
        req_template = ''' FROM  annotator_token
        LEFT JOIN annotator_morphology
        ON annotator_token.id = annotator_morphology.token_id
        LEFT JOIN annotator_annotation
        ON annotator_token.sent_id = annotator_annotation.document_id
        WHERE 1 AND lem="%s" AND num>= annotator_annotation.start AND num <= annotator_annotation.end %s %s''' %(word,parse_gram(err, 'tag'), parse_gram(gram, 'gram'))
        if flag:
            req_template += 'AND doc_id IN ('+','.join(docs)+')'
        n_req = '''SELECT COUNT(DISTINCT sent_id)''' + req_template
        req = 'SELECT DISTINCT sent_id, num' + req_template
        req1 = 'SELECT DISTINCT sent_id' + req_template
        d_req = '''SELECT COUNT(DISTINCT doc_id)''' + req_template
    elif s == '1100':
        req_template = ''' FROM  annotator_morphology
        LEFT JOIN annotator_token
        ON annotator_token.id = annotator_morphology.token_id
        WHERE 1 AND lem="%s" %s''' %(word, parse_lex(lex))
        if flag:
            req_template += 'AND doc_id IN ('+','.join(docs)+')'
        n_req = '''SELECT COUNT(DISTINCT sent_id)''' + req_template
        req = 'SELECT DISTINCT sent_id, num' + req_template
        req1 = 'SELECT DISTINCT sent_id' + req_template
        d_req = '''SELECT COUNT(DISTINCT doc_id)''' + req_template
    elif s == '1101':
        req_template = ''' FROM  annotator_token
        LEFT JOIN annotator_morphology
        ON annotator_token.id = annotator_morphology.token_id
        LEFT JOIN annotator_annotation
        ON annotator_token.sent_id = annotator_annotation.document_id
        WHERE 1 AND lem="%s" AND num>= annotator_annotation.start AND num <= annotator_annotation.end %s %s''' %(word,parse_gram(err, 'tag'), parse_lex(lex))
        if flag:
            req_template += 'AND doc_id IN ('+','.join(docs)+')'
        n_req = '''SELECT COUNT(DISTINCT sent_id)''' + req_template
        req = 'SELECT DISTINCT sent_id, num' + req_template
        req1 = 'SELECT DISTINCT sent_id' + req_template
        d_req = '''SELECT COUNT(DISTINCT doc_id)''' + req_template
    elif s == '1110':
        req_template = ''' FROM  annotator_token
        LEFT JOIN annotator_morphology
        ON annotator_token.id = annotator_morphology.token_id
        WHERE 1 AND lem="%s" %s %s ''' %(word, parse_lex(lex), parse_gram(gram, 'gram'))
        if flag:
            req_template += 'AND doc_id IN ('+','.join(docs)+')'
        n_req = '''SELECT COUNT(DISTINCT sent_id)''' + req_template
        req = 'SELECT DISTINCT sent_id, num' + req_template
        req1 = 'SELECT DISTINCT sent_id' + req_template
        d_req = '''SELECT COUNT(DISTINCT doc_id)''' + req_template
    else:
        req_template = ''' FROM  annotator_token
        LEFT JOIN annotator_morphology
        ON annotator_token.id = annotator_morphology.token_id
        LEFT JOIN annotator_annotation
        ON annotator_token.sent_id = annotator_annotation.document_id
        WHERE 1 AND lem="%s" AND num>= annotator_annotation.start AND num <= annotator_annotation.end %s %s %s''' %(word,parse_gram(err, 'tag'), parse_lex(lex), parse_gram(gram, 'gram'))
        if flag:
            req_template += 'AND doc_id IN ('+','.join(docs)+')'
        n_req = '''SELECT COUNT(DISTINCT sent_id)''' + req_template
        req = 'SELECT DISTINCT sent_id, num' + req_template
        req1 = 'SELECT DISTINCT sent_id' + req_template
        d_req = '''SELECT COUNT(DISTINCT doc_id)''' + req_template
    req1 += ' LIMIT %d,%d;' %((page - 1)*per_page, per_page)

    sentences = '(' + ', '.join([str(i[0]) for i in db.execute(req1)]) + ')'
    if sentences == '()':
        return [], 0, 0
    if s == '0001':
        req += ' AND document_id IN ' + sentences
    else:
        req += ' AND sent_id IN ' + sentences
    f = codecs.open('/home/elmira/heritage_corpus/tempfiles/s.txt', 'w')
    f.write(req + '\r\n' + n_req + '\r\n' + d_req)
    f.close()
    rows = db.execute(req)
    sent_num = int(db.execute(n_req)[0][0])
    d_num = int(db.execute(d_req)[0][0])
    return rows, sent_num, d_num


def parse_lex(lex):
    req = ''
    arr = ['lex LIKE "' + gr.strip() + '"' for gr in lex.replace(')', '').replace('(', '').split('|')]
    if len(arr) == 1:
        req += 'AND '+ arr[0] + ' '
    else:
        req += 'AND (' + ' OR '.join(arr) + ') '
    return req


def parse_gram(gram, t):
    req = ''
    arr = gram.split(',')
    for gr in arr:
        one = [t + ' LIKE "%' + i.strip() + '%"' for i in gr.replace(')', '').replace('(', '').split('|')]
        if len(one) == 1:
            req += 'AND '+ one[0] + ' '
        else:
            req += 'AND (' + ' OR '.join(one) + ') '
    return req


def bincode(a,b,c,d):
    s = ''
    for i in [a,b,c,d]:
        s += '1' if i else '0'
    return s