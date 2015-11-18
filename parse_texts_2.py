# coding=utf-8
from django.utils import timezone
import sys, os, codecs, datetime
import re
import json, uuid
# note: the path is hardcoded on the next line. change accordingly.
sys.path.append('C:/Users/Admin/OneDrive/PycharmProjects/learner_corpus/learner_corpus')
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

from annotator.models import Document, Sentence, Token, Morphology, Annotation
import django
django.setup()

reSpace = re.compile(u'\\s+',flags=re.U)

students = []

docs, se, wo, mo, annotations, ob = 0, 0, 0, 0, 0, 0

all_fixtures = []

d = [i.split('\t') for i in codecs.open('error_dict.txt', 'r', 'utf-8').read().split('\r\n')]
dict = {i[0]: i[1].split(',') for i in d}

class Struct:
    def __init__(self, **values):
        vars(self).update(values)

    def makesent(self):
        result = u''
        for num in range(len(self.words)):
            if num != 0:
                if self.words[num].punctl != self.words[num - 1].punctr:
                    result += self.words[num].punctl
                result += self.words[num].text + self.words[num].punctr + ' '
            else:
                result += self.words[num].punctl + self.words[num].text + self.words[num].punctr + ' '
        self.sentence = reSpace.sub(' ', result)
        # print self.sentence


def make_tagged_sent(words):
    result = u''
    for num in range(len(words)):
        tooltip, punctl, token, punctr = words[num][0], words[num][1], words[num][2], words[num][3]
        if num != 0:
            if punctl != words[num - 1][3]:
                result += punctl
            result += '<span class="token" data-toggle="tooltip" title="' + tooltip + '">' + token + '</span>' + punctr + ' '
        else:
            result += punctl + '<span class="token" data-toggle="tooltip" title="' + tooltip + '">' + token + '</span>' + punctr + ' '
    return result


def split_err_from_gram(tags):
    tags = tags.split(',')
    gram = []
    err = []
    for tag in tags:
        if tag not in dict:
            gram.append(tag)
        else:
            err += dict[tag]
    return ' '.join(gram), err



def tooltip_generator(anas):
    d = {}
    for ana in anas:
        lem = ana.lem
        bastard = False
        if 'qual="' in lem:
            lem = lem.split('"')[0]
            bastard = True
        lex, gram = ','.join(ana.lex.split(' ')), ','.join(ana.gram.split(' '))
        if bastard:
            lex = 'bastard,' + lex
        if lem + ', ' + lex not in d:
            d[lem + ', ' + lex] = gram
        else:
            d[lem + ', ' + lex] += '<br>' + gram
    arr = ['<b>'+key+'</b><br>' + d[key] for key in d]
    return '<hr>'.join(arr)
    # todo generate tooltip with morpho <- merge similar morphos!!


def get_prs(fname):
    global docs, se, wo, mo, annotations, all_fixtures, ob, fixt, fixt_num, started_file
    last = ''
    prs = codecs.open(fname, 'r', 'utf-8')
    if ob > 10000:
        fixt.write(']')
        fixt.close()
        fixt_num += 1
        fixt = codecs.open(u'fixtures\\fixtures'+str(fixt_num)+'.json', 'a', 'utf-8')
        fixt.write('[')
        started_file = True
        ob = 0
    meta = {}
    sents = []
    prev_sentno = 0
    prev_wordno = 0
    err_start = 0
    err_end = 0
    words = 0
    correction = ''
    for line in prs:
        if line.startswith('#sentno') or line.startswith('#meta.issue') or line.startswith('#meta.docid'):
            continue
        if line == '\r\n':
            continue
        line = line.strip('\r\n')
        if line.startswith('#'):
            field, value = line[6:].split('\t')
            meta[field.replace('-', '_')] = value
            if meta['author'] != '':
                if meta['author'] in students:
                    student_code = students.index(meta['author']) + 1
                else:
                    students.append(meta['author'])
                    student_code = len(students)
            else:
                student_code = 0
            meta['student_code'] = student_code
            if field in ['date1', 'date2', 'words', 'sentences', 'university-code', 'term', 'module']:
                if value == u'':
                    meta[field.replace('-', '_')] = 0
                else:
                    meta[field.replace('-', '_')] = int(re.search('\\d+', value).group())
        else:
            # print line
            in_corr = False
            in_err = False
            end_err = False
            end_corr = False
            try:
                sentno, wordno, lang, graph, word, indexword, nvars, nlems, nvar, lem, trans, trans_ru, lex, gram, flex, punctl, punctr, sent_pos = line.split('\t')
            except ValueError:
                print line
            if '} / {*' in punctl:
                in_corr = True
                in_err = False
                end_err = False
            elif '{' in punctl:
                in_corr = False
                err_start = words+1
                in_err = True
                end_corr = False
            if '} / {*' in punctr:
                err_end = words+1
                end_corr = False
                end_err = True
            elif '}' in punctr:
                end_corr = True
                in_err = False
            punctl, punctr = punctl.replace('\\n', '').replace('} / {*', '').replace('{', ''), \
                             punctr.replace('\\n', '').replace('} / {*', '').replace('}', '')

            if in_corr:
                print 'in corr'
                correction += punctl.replace('} / {*', '').replace('{', '') + word + punctr.replace('} / {*', '').replace('}', '') + ' '
                continue
            else:
                gram, err = split_err_from_gram(gram)
                if nvars != '':
                    nvars = int(nvars)
                sentno, wordno, nlems, nvar = int(sentno), int(wordno), int(nlems), int(nvar)
                if end_err:
                    ana = Struct(lem=lem, lex=lex, gram=gram, err=err)
                elif in_err:
                    ana = Struct(lem=lem, lex=lex, gram=gram, err=[])
                else:
                    ana = Struct(lem=lem, lex=lex, gram=gram, err=err)
                if end_corr:
                    ana.corr = correction
                    correction = ''
                    ana.start = err_start
                    ana.end = err_end
                    err_start = 0
                    err_end = 0
                if sentno != prev_sentno:
                    if wordno != prev_wordno:
                        # print 'nw'
                        words += 1
                        w = Struct(num=words,text=word,
                            punctl=punctl,punctr=punctr,sent_pos=sent_pos, ana=[ana])

                        # print w.text
                    else:
                        w.ana.append(ana)
                    sents.append(Struct(num=sentno,words=[w]))
                else:
                    if wordno != prev_wordno:
                        # print word
                        words += 1
                        w = Struct(num=words, text=word,
                                   punctl=punctl, punctr=punctr, sent_pos=sent_pos, ana=[ana])

                        # print w.text
                        sents[-1].words.append(w)
                    else:
                        w.ana.append(ana)

                if sent_pos == 'eos' and (nvars == nvar or nvars==''):
                    prev_wordno = 0
                    words = 0
                else:
                    prev_wordno = wordno
                prev_sentno = sentno
                # print len(sents[-1].words)
    meta["body"] = 'loaded from xml'
    meta['sentences'] = len(sents)
    meta['words'] = sum(len(i.words) for i in sents)
    meta["created"] = str(timezone.now())
    if u'D:\Документы\Рабочий стол\parsed_data\pr\\' in fname:
        meta["checked"] = True
    meta['filename'] = fname.replace(u'D:\Документы\Рабочий стол\parsed_data', '')
    docs += 1
    arr = []
    d_dict = {"fields": meta, "model": "annotator.document", "pk": docs}
    # print(meta)
    prs.close()
    for i in xrange(len(sents)):
        sents[i].makesent()
        # print '.',
        se += 1
        se_dict = {"fields": {"text": sents[i].sentence, "tagged": "", "num": i, "doc_id": docs},
                   "model": "annotator.sentence",
                   "pk": se}
        ob += 1
        stagged = []
        for k in range(len(sents[i].words)):
            w = sents[i].words[k]
            wo += 1
            w_dict = {"fields": {"punctr": w.punctr,
                                 "doc": docs,
                                 "token": w.text,
                                 "num": w.num,
                                 "punctl": w.punctl,
                                 "sent_pos": w.sent_pos,
                                 "sent": se},
                      "model": "annotator.token",
                      "pk": wo}
            ob += 1
            arr.append(w_dict)
            for a in w.ana:
                mo += 1
                m_dict = {"fields": {"lex": a.lex, "token": wo, "lem": a.lem, "gram": a.gram},
                          "model": "annotator.morphology",
                          "pk": mo}
                arr.append(m_dict)
                ob += 1
            tok = (tooltip_generator(w.ana), w.punctl, w.text, w.punctr)
            if w.ana[0].err != []:
                annotations += 1
                if 'corr' in vars(w.ana[0]):
                    a_dict = {"fields": {"document": se,
                                     "created": str(timezone.now()),
                                     "updated": str(timezone.now()),
                                     "end": w.ana[0].end,
                                     "start": w.ana[0].start,
                                     "tag": ', '.join(w.ana[0].err),
                                     "guid": str(uuid.uuid4()),
                                     "data": json.dumps({"ranges": [{"start": "/span["+w.ana[0].start+"]", "end": "/span["+w.ana[0].end+"]", "startOffset": 0, "endOffset": len(w.punctl + w.text + w.punctr)}], "quote": w.text, "text": "", "corrs": w.ana[0].corr, "tags": w.ana[0].err, "readonly": False})},
                          "model": "annotator.annotation",
                          "pk": annotations}
                else:
                    a_dict = {"fields": {"document": se,
                                         "created": str(timezone.now()),
                                         "updated": str(timezone.now()),
                                         "end": str(k+1),
                                         "start": str(k+1),
                                         "tag": ', '.join(w.ana[0].err),
                                         "guid": str(uuid.uuid4()),
                                         "data": json.dumps({"ranges": [{"start": "/span["+str(k+1)+"]", "end": "/span["+str(k+1)+"]", "startOffset": 0, "endOffset": len(w.punctl + w.text + w.punctr)}], "quote": w.text, "text": "", "corrs": '', "tags": w.ana[0].err, "readonly": False})},
                              "model": "annotator.annotation",
                              "pk": annotations}
                ob += 1
                arr.append(a_dict)
                d_dict["fields"]["annotated"] = True
            stagged.append(tok)
        se_dict["fields"]["tagged"] = make_tagged_sent(stagged)
        arr.append(se_dict)
    ob += 1
    if started_file is not True:
        if last != ', ':
            fixt.write(', ')
            last = ', '
    fixt.write(json.dumps(d_dict))
    last = json.dumps(d_dict)
    if started_file is True:
        started_file = False
    if last != ', ':
        fixt.write(', ')
        last = ', '
    fixt.write(', '.join([json.dumps(i) for i in arr[::-1]]))
    last = 'arrr'
    print len(sents)


if __name__ == "__main__":
    fixt_num = 0
    fixt = codecs.open(u'fixtures\\fixtures'+str(fixt_num)+'.json', 'a', 'utf-8')
    fixt.write('[')
    started_file = True
    for root, dirs, files in os.walk(u'./texts_for_testing'):
        for i in files:
            if i.endswith('.prs'):
                p = os.path.join(root, i)
                print p
                if docs % 100 == 0 and docs != 0:
                    print 'PROCESSED DOCS:', docs
                get_prs(p)


