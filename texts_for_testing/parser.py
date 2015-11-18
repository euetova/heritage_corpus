# coding=utf-8

import sys, os, codecs
import re
# from itertools import islice
import json, uuid
sys.path.append('/home/mesh/heritage_corpus/heritage_corpus')
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

from annotator.models import Document, Sentence, Token, Morphology, Annotation
import django
django.setup()

reSpace = re.compile(u'\\s+',flags=re.U)

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
        return self.sentence


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


def gram_to_list(tag):
    """
    :param tag: "morpho?,calque 'sssss'"
    :return: ['morph', '?', 'calque'], sssss
    """
    typo = {'mot-clear': 'not-clear',
            'morpho': 'morph',
            'moprh': 'morph',
            'moerph': 'morph',
            'not clear': 'not-clear'}
    tag = re.sub('\?', ' ? ', tag)
    tag = re.sub('/', ' / ', tag)
    source = ''
    tag = re.sub(u"(\u2018|\u2019|\xe2\x80\x99|'|\")+", "@", tag)
    # tag = re.sub("[(\xe2\x80\x99)'\"]+", "@", tag)
    find_a = re.search('@(.*?)@', tag)
    if find_a:
        source = find_a.group(1)
    tag = re.sub("@(.*)@", " ", tag)
    tag_list = filter(None, re.split("[, !=:]+", tag))
    # print 'list: ', tag_list
    corrected = []
    for word in tag_list:
        if word in typo.keys():
            corrected.append(typo[word])
        else:
            corrected.append(word)
    return corrected, source


def tooltip_generator(anas):
    d = {}
    for ana in anas:
        lem = ana.lem
        # print ana, type(ana)
        # print 'lem', lem, type(lem)
        # bastard = False
        # if 'qual="' in lem:
        #     lem = lem.split('"')[0]
        #     bastard = True
        lex = ana.lex
        gram = ','.join(ana.gram)
        # if bastard:
            # lex = 'bastard,' + lex
        if lem + ', ' + lex not in d:
            d[lem + ', ' + lex] = gram
        else:
            d[lem + ', ' + lex] += '<br>' + gram
    arr = ['<b>'+key+'</b><br>' + d[key] for key in d]
    return '<hr>'.join(arr)

def get_prs(fname):
    prs = codecs.open(fname, 'r', 'utf-8')
    meta = {}
    meta[u"body"] = u''     # WHY ON EARTH ARE WE DOING IT?
    meta[u"subcorpus"] = u'RULEC'
    sents = []
    prev_sentno = 0
    prev_wordno = 0

    meta_fields = ['author', 'title', 'date1', 'date2', 'genre', 'gender', 'language_background', 'level', 'course',
                   'text_type', 'issue', 'words', 'sentences', 'date_displayed']
    for line in prs:
        if line.startswith('#sentno') or line.startswith('#meta.issue') or line.startswith('#meta.docid'):
            continue


        if line.startswith('#'):
            # print [line]
            # line = line.strip('[\t\r\n]+') if line.endswith('\t\n') else line.strip('[\r\n]+')
            line = re.sub('\t{2,}', '', line)
            line = line.strip('[\r\n]+')
            field, value = line[6:].split('\t')
            # r = re.search("^#meta\.\t(<field>)", line)
            # r.groups()
            # print r
            meta_field = field.replace(u'-', u'_')
            if meta_field in meta_fields:
                if len(value) > 0 and value != u'–':
                    meta[meta_field] = value
                else:
                    meta[meta_field] = ' '
            # print meta
        else:
            line = line.strip('[\r\n]+')
            # line = line.strip('[\r\n]+')
            # print [line]
            # print line.count('\t')
            [sentno, wordno, lang, graph, word, indexword, nvars, nlems, nvar, lem, trans, trans_ru, lex, gram, flex, punctl, punctr, sent_pos] = line.split('\t')
            tag_list, source = [], ''
            tag_list, source = gram_to_list(gram)
            errors = [u'?', u'/', u'+', u'orpho', u'gov', u'Cs', u'typo', u'graph', u'phon', u'morph', u'coord', u'asp',
                      u'constr', u'lex', u'calque', u'GraphCalque', u'MorphCalque', u'ConstrCalque', u'LexCalque',
                      u'SyntaxCalque', u'qsicalque', u'not-clear', u'syntax', u're']
            # check the list of errors
            gram = []
            err = []
            for g in tag_list:          # l.lower()
                if g not in errors:
                    gram.append(g)
                else:
                    err.append(g)
            punctr = re.sub('0', '', punctr)

            ana = Struct(lem='', lex='', gram='')
            # print 'reading', sentno, wordno, word, trans

            if nvar <= nvars:                    # always true?
                ana = Struct(lem=lem, lex=lex, gram=gram)
            if sentno != prev_sentno:           # next sentence
                if wordno != prev_wordno:       # next word
                    # if trans != word and len(trans.split) > 0:
                    #     constr = len(trans.split)
                    # if punctl == "} / {*" or constr == 0:
                    #     constr -= 1
                    #     continue
                    w = Struct(num=wordno, text=word, punctl=punctl, punctr=punctr, sent_pos=sent_pos,
                               err=err, source=source, corrected=trans, ana=[ana])


                else:                           # word continued
                    w.ana.append(ana)           # another ana of the word

                sents.append(Struct(num=sentno,words=[w]))
            else:                               # sentence continued
                if wordno != prev_wordno:       # next word
                    w = Struct(num=wordno, text=word, punctl=punctl, punctr=punctr, sent_pos=sent_pos,
                               err=err, source=source, corrected=trans, ana=[ana])
                    sents[-1].words.append(w)
                else:                           # word continued
                    w.ana.append(ana)

            if sent_pos == 'eos' and nvars == nvar:
                prev_wordno = 0
            else:
                prev_wordno = wordno
            prev_sentno = sentno
            # print len(sents[-1].words)
    prs.close()
    print 'hello'
    # for s in sents:
        # for w in s.words:
        #     if len(w.corrected.split()) > 1:
        #         print 's', s.num, ' '.join([w.text + w.punctr for w in s.words])
        #         pos = s.words.index(w)
        #         step = len(w.corrected.split())
        #         # print ' '.join([i.text for i in s.words[pos+1:pos+step+1]])
        #         print step, 'skip', ' '.join([t.text for t in s.words[pos+1:pos+step+2]])
        #         s.words[pos+1+ (len_orig - 1):pos+lstep+2] = []
        #
        # print 's !', ' '.join([w.num + ' ' + w.corrected + w.punctr for w in s.words])

    # sents_iter = iter(sents)
    # for i in xrange(len(sents)):
    for s in sents:
        in_anno = False
        print 's', s.num, ' '.join([q.text for q in s.words])
        for w in s.words:
            # if w != wce:
            if not in_anno:
                mis_use = {}
                print 'w', w.num, w.text, w.corrected
                if w.corrected != w.text:
                    mis_use = {'start': w.num, 'end': w.num, 'corrected': w.corrected, 'cor_start': w.num, 'cor_end': w.num, 'tags': w.err, 'source': w.source}
                    if w.punctl == '{':
                        in_anno = True
                        for we in s.words[s.words.index(w):]:
                            if we.punctr == '} / {*':
                                mis_use['end'] = we.num
                                for wc in s.words[s.words.index(we)+1:]:
                                    if wc.punctl == '} / {*':
                                        mis_use['cor_start'] = wc.num
                                        for wce in s.words[s.words.index(wc):]:
                                            if wce.punctr == '}':
                                                mis_use['cor_end'] = wce.num
                                                print mis_use
                                                in_anno = False
                                                # step = int(mis_use['cor_end'])-int(mis_use['start'])+3
                                                # [sents_iter.next() for x in range(step)]
                                                break
                                        break
                                break
                    else:
                        # one-word error
                        print '1word error', w.text, w.corrected
                        # print mis_use['start'], mis_use['end'], mis_use['cor_start'], mis_use['cor_end']
                    print 'mis_use', w.num, w.text, mis_use['corrected']






    # doc, created = Document.objects.get_or_create(**meta)
    # print 'document created!\nmeta: ', meta
    #
    # for i in xrange(len(sents)):
    #     print i, sents[i].makesent()
    #     sent, created = Sentence.objects.get_or_create(text=sents[i].sentence,
    #                                           doc_id=doc,
    #                                           num=i)
    #     stagged = []
    #     for k in range(len(sents[i].words)):
    #
    #         w = sents[i].words[k]
    #
    #         word, created = Token.objects.get_or_create(token=w.text,
    #                                            doc=doc,
    #                                            sent=sent,
    #                                            num=w.num,
    #                                            punctl=w.punctl,
    #                                            punctr=w.punctr,
    #                                            sent_pos=w.sent_pos)
    #
    #         for a in w.ana:
    #             Morphology.objects.get_or_create(token=word,
    #                                              lem=a.lem,
    #                                              lex=a.lex,
    #                                              gram=a.gram)
    # #             d = {}
    # #             lex = a.lex
    # #             lem = a.lem
    # #             gram = ','.join(ana.gram)
    # #             if lem + ', ' + lex not in d:
    # #                 d[lem + ', ' + lex] = gram
    # #             else:
    # #                 d[lem + ', ' + lex] += '<br>' + gram
    # # # arr = ['<b>'+key+'</b><br>' + d[key] for key in d]
    # # # return '<hr>'.join(arr)
    # # word = ' <span class="token" title="' + all_ana + '">' + \
    # #         w.punctl + token.token + token.punctr + '</span> '
    # # stagged.append(word)
    # # sent.tagged = ''.join(stagged)
    # # sent.correct = sent.tagged
    #
    #
    #         tok = (tooltip_generator(w.ana), word.punctl, word.token, word.punctr)
    #         # if k != len(sents[i].words) - 1:
    #         #     offset = len(word.punctl + word.token + word.punctr+ '</span>' '<span class="token" data-toggle="tooltip" title="') + len(tooltip_generator(sents[i].words[k+1].ana) + '">')
    #         # else:
    #         #     offset = 100
    #         # print tooltip_generator(w.ana), word.punctl, word.token, word.punctr
    #
    #         # print 'w ana', w.ana[0].lem
    #         if w.ana[0].err != []:
    #             # print '!', w.ana[0].corrected
    #             annot, created = Annotation.objects.get_or_create(document=sent, guid=str(uuid.uuid4()),
    #                                                               data=json.dumps({"ranges": [{"start": "/span["+str(k+1)+"]",
    #                                                                           "end": "/span["+str(k+1)+"]",
    #                                                                           "startOffset": 0,
    #                                                                           "endOffset": len(word.punctl + word.token + word.punctr)}],
    #                                                                           "quote": w.text,
    #                                                                           "text": w.ana[0].source,
    #                                                                           "tags": ''}),
    #                                                               corr=w.ana[0].corrected)
    #
    #             d = json.loads(annot.data)
    #             d['readonly'] = False
    #             annot.data = json.dumps(d)
    #             annot.tag = ', '.join(w.ana[0].err)
    #             # annot.corrs = w.ana[0].corrected
    #             # d['corrs'] = w.ana[0].corrected
    #
    #             # print 'start', d["ranges"][0]['start']
    #             annot.save()
    #             doc.annotated = True
    #             doc.body = 'loaded from xml'
    #             doc.save()
    #         stagged.append(tok)
    #     sent.tagged = make_tagged_sent(stagged)
    #     sent.save()
    # print 'len of sents: ', len(sents)
    # print Annotation.objects.all()




if __name__ == "__main__":
    for root, dirs, files in os.walk(u'/home/mesh/heritage_corpus/texts'):
        for f in files:
            if f.endswith('.prs'):
                p = os.path.join(root, f)
                print 'document ', p
                get_prs(p)
