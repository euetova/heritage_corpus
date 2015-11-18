# coding=utf-8
import sys, os, codecs
import re
import json, uuid, codecs
sys.path.append('C:/Users/Admin/OneDrive/PycharmProjects/heritage_corpus/heritage_corpus')
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

from django.contrib import admin
from annotator.models import Document, Sentence, Token, Morphology, Annotation
import django
django.setup()

from annotator.models import Document, Sentence, Annotation, Token, Morphology

def parse_data(data):
    s = json.loads(data)
    corrs, quote, start, end = s['corrs'], s['quote'], \
                           int(s["ranges"][0]['start'].replace('/span[', '').replace(']', '')), \
                           int(s["ranges"][0]['start'].replace('/span[', '').replace(']', ''))
    return corrs, quote, start, end

# with codecs.open(u'table.csv', 'w', 'cp1251') as f:
#     f.write(u'Разметчик\tТекст\tПредложение\tНомер предложения в тексте\tТэг\tОшибка\tИсправление\r\n')
#     for ann in Annotation.objects.all():
#         if ann.owner is not None and ann.owner.username != 'admin':
#             c, q = parse_data(ann.data)
#             f.write(str(ann.owner))
#             f.write('\t')
#             f.write(str(ann.document.doc_id))
#             f.write('\t')
#             f.write(unicode(ann.document))
#             f.write('\t')
#             f.write(unicode(ann.document.num))
#             f.write('\t')
#             f.write(unicode(ann.tag))
#             f.write('\t')
#             f.write(q)
#             f.write('\t')
#             f.write(c)
#             f.write('\r\n')

with codecs.open(u'table.csv', 'w', 'cp1251') as f:
    f.write(u'Текст\tНомер предложения в тексте\tСлово\tНомер слова\tРазметчик\tТэги\tОшибка\r\n')
    for doc in Document.objects.all():
        for sent in doc.sentence_set.all():
            for word in sent.token_set.all():
                has_ann = False
                for ann in sent.annotation_set.all():
                    c, q, start, end = parse_data(ann.data)
                    if word.num <= end and word.num >= start:
                        arr = [unicode(doc), str(sent.num), unicode(word), str(word.num), str(ann.owner), unicode(ann.tag), q]
                        has_ann = True
                        f.write('\t'.join(arr))
                        f.write('\r\n')
                if has_ann is False:
                    arr = [unicode(doc), str(sent.num), unicode(word), str(word.num), '','','']
                    f.write('\t'.join(arr))
                    f.write('\r\n')
