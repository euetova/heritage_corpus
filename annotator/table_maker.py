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


def parse_data(data):
    s = json.loads(data)
    for i in s:
        text = i['text']
        data = json.loads(i['data'])
        corr = data['corrs']
        tag = i['tag']
        quote = data['quote']
        print '\t'.join([tag, text, quote, corr])

with codecs.open('annotator_sentence.json', 'r', encoding='utf-8') as f:
    parse_data(f.read())




