# coding=utf-8

# Django modules
from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _

# My modules
from TestCorpus.db_utils import Database
from utils import *

# Standard modules
import json

# находит тэги span с окружающими знаками препинания
regSpan = re.compile('[.?,!:«(;#№–/...)»-]*<span .*?</span>[.?,!:«(;#№–/...)»-]*', flags=re.U | re.DOTALL)

# находит слово с окружающими знаками препинания
regWord = re.compile('([.?,!:«(;#№–/...)»-]*)(\\w+)([.?,!:«(;#№–/...)»-]*)', flags=re.U | re.DOTALL)

# нужно, чтобы добавлять разметку в окне выдачи
bold_regex = re.compile('/b\\[(\\d+)\\]')  # нужно, чтобы добавлять разметку в окне выдачи
span_regex = re.compile('span\\[(\\d+)\\]')

# опции для выбора в окне метаразметки
NativeChoices = ((u'eng', _(u'English')), (u'nor', _(u'Norwegian')), (u'kor', _(u'Korean')),
                 (u'ita', _(u'Italian')), (u'fr', _(u'French')), (u'ger', _(u'German')),
                 (u'ser', _(u'Serbian')))
ModeChoices = ((u'п', _(u'written')), (u'у', _(u'oral')))
GenderChoices = ((u'ж', _(u'female')), (u'м', _(u'male')))
BackgroundChoices = ((u'HL', _(u'heritage')), (u'FL', _(u'foreign')))


class Document(models.Model):
    """
    Хранит информацию об одном тексте.

    Свойства текста:
    owner - пользователь, который добавил текст, связан с :models:`auth.User`
    created - дата и время, когда текст был добавлен
    title - название текста, генерируется автоматически из жанра, типа текста и курса
    body - сам текст, если он был добавлен разметчиком вручную;
        если текст был перезалит из старой платформы, то в этом атрибуте хранится строка "loaded from xml"
    author - автор текста
    mode - устный или письменный
    filename - источник текста
    subcorpus - название подкорпуса
    date1 - дата начала написания текста (или первый год в записи учебного года, например, 2010-2011)
    date2 - дата окончания написания текста (или второй год в записи учебного года, например, 2010-2011)
    genre - жанр текста
    gender - пол автора
    course - курс, в рамках которого текст был задан
    language_background - русский язык является иностранным или эритажным
    text_type - тип текста
    level - уровень
    annotation - автоматическая или ручная аннотация (осталось от РУЛЕКа)
    student_code - код студента (возможно он не нужен)
    time_limit - временные ограничения (осталось от РУЛЕКа)
    native - родной/доминантный язык автора
    fullmeta - полностью ли заполнены релевантные поля метаразметки
    words - количество слов в тексте
    sentences - количество предложений в тексте
    date_displayed - отображаемая дата
    annotated - размечен ли текст
    checked - проверен ли текст
    """
    owner = models.ForeignKey(User, blank=True, null=True, verbose_name=_('owner'))
    created = models.DateTimeField(auto_now_add=True, db_index=True)
    title = models.CharField(max_length=250, db_index=True, null=True, blank=True, editable=True, verbose_name=_('название'))
    body = models.TextField(help_text=_("Paste the text here."), verbose_name=_('text'))  # HTML
    # todo probably should delete this field and create a special form in admin
    author = models.CharField(max_length=100, help_text=_("Enter author's first and/or  second name."), verbose_name=_('author'))
    mode = models.CharField(max_length=50, null=True, blank=True, db_index=True, verbose_name=_('mode'), choices=ModeChoices)
    filename = models.CharField(max_length=5000, help_text=_("Enter the name of the folder and file from which the text is taken."), verbose_name=_('Source'))
    subcorpus = models.CharField(max_length=5000, null=True, blank=True, verbose_name=_('subcorpus'))

    # optional fields - need them for meta in CoRST
    date1 = models.IntegerField(null=True, blank=True, help_text=_("When the text was written, e.g. 2014."), verbose_name=_('date'))
    date2 = models.IntegerField(null=True, blank=True)
    genre = models.CharField(max_length=100, null=True, blank=True, db_index=True, verbose_name=_('genre'))
    gender = models.CharField(max_length=5, null=True, blank=True, db_index=True, verbose_name=_('gender'), choices=GenderChoices)
    course = models.CharField(max_length=100, null=True, blank=True, db_index=True, help_text=_("Enter the name of the program in which the text was assigned"), verbose_name=_('program'))
    language_background = models.CharField(max_length=100, null=True, blank=True, db_index=True, verbose_name=_('language background'), choices=BackgroundChoices)
    text_type = models.CharField(max_length=100, null=True, blank=True, db_index=True, verbose_name=_('type of text'))
    level = models.CharField(max_length=100, null=True, blank=True, db_index=True, verbose_name=_('level'))
    annotation = models.CharField(max_length=100, null=True, blank=True, db_index=True, verbose_name=_('annotation'))
    student_code = models.IntegerField(null=True, blank=True, verbose_name=_('student code'))
    time_limit = models.CharField(max_length=100, null=True, blank=True, verbose_name=_('time limit'))
    native = models.CharField(max_length=10, null=True, blank=True, choices=NativeChoices, db_index=True, verbose_name=_('dominant language'))
    fullmeta = models.NullBooleanField(null=True, blank=True, verbose_name=_('full metadata'))

    # needed for general corpus statistics
    words = models.IntegerField(editable=True, null=True, blank=True, verbose_name=_('words'))
    sentences = models.IntegerField(editable=False, null=True, blank=True, verbose_name=_('sentences'))
    date_displayed = models.CharField(editable=False, max_length=50, null=True, blank=True, verbose_name=_('date displayed'))

    # needed for annotation statistics
    annotated = models.BooleanField(default=False, verbose_name=_('text is annotated'))
    checked = models.BooleanField(default=False, verbose_name=_('text is checked'))

    class Meta:
        verbose_name = _('document')
        verbose_name_plural = _('documents')

    def __unicode__(self):
        return self.title + ', ' + self.author if self.title else '- , ' + self.author

    def save(self, **kwargs):
        """
        Сохраняет текст в базу данных.

        Если текст уже был ранее загружен в базу данных (т.е. пользователь редактирует старый текст),
        то в базе данных только обновляется метаинформация.
        Если добавляется новый текст, то для него генерируется название из метаполей,
        сам текст обрабатывается майстемом, информация о словах и предложениях записывается
        в базу и связывается с соответствующей тексту строкой базы данных.
        """
        handle_sents = False
        if self.id is None:
            handle_sents = True
        if self.date1 and self.date2:
            if self.date1 == self.date2:
                self.date_displayed = self.date1
            else:
                self.date_displayed = str(self.date1) + '-' + str(self.date2)
        genre = self.genre if self.genre else ' -'
        course = self.course if self.course else '- '
        text_type = self.text_type if self.text_type else ' - '
        if self.title == '-' or self.title is None:
            self.title = genre + ' (' + text_type + ', ' + course + ')'
        super(Document, self).save()
        # todo how to close body change after a Document has been created?
        # we don't want people to change the texts after it has been parsed and loaded to the DB
        # but we want them to be able to edit meta
        if handle_sents:
            self.handle_sentences()

    def handle_sentences(self):
        """Отправляет текст в майстем и раскладывает результат в ячейки базы данных."""
        self.words, text = mystem(self.body)
        self.sentences = len(text)
        super(Document, self).save()
        for sent_id in range(len(text)):
            sent, created = Sentence.objects.get_or_create(text=text[sent_id].text, doc_id=self, num=sent_id+1)
            words = text[sent_id].words
            stagged = []
            for i_word in range(len(words)):
                sent_pos = ''
                if i_word == 0: sent_pos = 'bos'
                elif i_word == len(words) - 1: sent_pos = 'eos'
                token, created = Token.objects.get_or_create(doc=self, sent=sent, num=i_word+1,
                                                             sent_pos=sent_pos,
                                                             token=words[i_word].wf,
                                                             punctr=words[i_word].pr,
                                                             punctl=words[i_word].pl)
                analyses = words[i_word].anas
                all_ana = words[i_word].tooltip
                for ana in analyses:
                    lem = ana[0]
                    bastard = False
                    if 'qual="' in lem:
                        lem = lem.split('"')[0]
                        bastard = True
                    lex, gram = ana[1].split('=')
                    if ',' in lex:
                        lex = lex.split(',')
                        gram = ','.join(lex[1:]) + ',' + gram
                        lex = lex[0]
                    if bastard:
                        gram = 'bastard,' + gram
                    Morphology.objects.get_or_create(token=token, lem=lem,
                                                     lex=lex, gram=gram)
                word = ' <span class="token" title="' + all_ana + '">' + \
                       token.punctl + token.token + token.punctr + '</span> '
                # todo rethink this piece
                # Tim says storing html is fine, since you never change it later and they do it in EANC, for example
                # but still, there must be a better implementation - absolutely not urgent
                stagged.append(word)
            sent.tagged = ''.join(stagged)
            sent.correct = sent.text
            sent.correct2 = sent.text
            sent.save()


class Sentence(models.Model):
    """
    Хранит одно предложение.

    Свойства предложения:
    text - предложение
    doc_id - номер текста, к которому относится предложение
    num - номер предложения в тексте
    tagged - html-код предложения (вместе с морфологическими разборами слов)
    correct - предложение со всеми исправлениями
    correct2 - предложение с исправлениями орфографических ошибок
    temp - не нужное поле (УДАЛИТЬ!)
    """
    text = models.TextField()
    doc_id = models.ForeignKey(Document)
    num = models.IntegerField()
    tagged = models.TextField()  # stores the html-piece
    correct = models.TextField()
    correct2 = models.TextField()
    temp = models.TextField(null=True, blank=True)  # stores the html-piece

    def __unicode__(self):
        return self.text

    class Meta:
        verbose_name = _('sentence')
        verbose_name_plural = _('sentences')


class Annotation(models.Model):
    """Хранит информацию о разметке.

    Поля аннотации:
    owner - пользователь, который создал аннотацию
    document - предложение, к которому была добавлена аннотация, связано с :model:`annotator.Sentence`
    guid - уникальный id
    created - дата и время, когда аннотация была создана
    updated - дата и время последнего редактирования данной аннотации
    data - информация о разметка для javascript в формате json
    tag - приписанные тэги в строку, через запятую
    start - номер слова предложения (начиная с 1), с которого начинается выделение
    end - номер слова предложения (начиная с 1), которым заканчивается выделение
    """
    # taken from Django-Annotator-Store
    owner = models.ForeignKey(User, db_index=True, blank=True, null=True)
    document = models.ForeignKey(Sentence, db_index=True)
    guid = models.CharField(max_length=64, unique=True, editable=False)
    created = models.DateTimeField(auto_now_add=True, db_index=True)
    updated = models.DateTimeField(auto_now=True, db_index=True)
    data = models.TextField()  # all other annotation data as JSON
    tag = models.CharField(max_length=200, null=True, blank=True, db_index=True)
    start = models.IntegerField(blank=True, null=True)
    end = models.IntegerField(blank=True, null=True)

    class Meta:
        verbose_name = _('annotation')
        verbose_name_plural = _('annotations')

    def set_guid(self):
        self.guid = str(uuid.uuid4())

    def can_edit(self, user):
        # if self.owner and self.owner != user and (not user or not user.has_perm('annotator.change_annotation')):
        #     return False
        if not user or not user.has_perm('annotator.change_annotation'):
            return False
        return True

    def get_sent_annotations(self, id):
        """
        Получает из базы данных все исправления к предложению с заданным id.

        :param id: номер предложения в базе данных
        :return: массив аннотаций к предложению
        Каждая аннотация добавляется в виде такого кортежа:
            (начало исправления INTEGER, конец исправления INTEGER,
            текст исправления, приписанные тэги в строку через запятую).
        Если исправления нет (а только приписан тэг\комментарий), то аннотация в массив не добавляется.
        Если в списке тэгов аннотации есть тэг "Del", обозначающий лишнее слово, то аннотация в массив добавляется
        (т.е. пустая строка исправления в этом случае сама по себе является исправлением).
        """
        db = Database()
        req = 'SELECT `tag`, `start`, `end`, `data` FROM  annotator_annotation WHERE document_id=%d' %id
        arr = []
        rows = db.execute(req)
        for row in rows:
            d = json.loads(row[3])
            corr = d['corrs']
            if corr != '' or 'Del' in row[0]:
                arr.append((int(row[1]), int(row[2]), corr, row[0]))
        return arr

    def make_correction(self, sentence, remarks):
        """
        Получает предложение и список исправлений, возвращает исправленное предложение.

        :param sentence: предложение (строка)
        :param remarks: массив кортежей, каждый кортеж = одно исправление
        :return: исправленное предложение (строка)

        Вокруг исправлений вставляются тэги '<span class="correction">' и '</span>',
        чтобы исправление рендерилось на странице с другим форматированием.
        """
        sentence = sentence.split()
        dictionary = dict()
        for word_num in range(len(sentence)):
            dictionary[word_num] = sentence[word_num]
        for el in remarks:
            corr_start, corr_end, corr, tag = el
            r = range(corr_start-1, corr_end)
            dictionary[r[0]] = '<span class="correction">' + corr + '</span>'
            for i in r[1:]:
                dictionary[i] = ''
        s = ' '.join(dictionary[i] for i in sorted(dictionary) if dictionary[i] != '')
        return s

    def make_ortho_correction(self, sentence, remarks):
        """
        Получает предложение и список исправлений, возвращает предложение,
        в котором исправлены только орфографические (однословные) ошибки.

        :param sentence: предложение (строка)
        :param remarks: массив кортежей, каждый кортеж = одно исправление
        :return: исправленное предложение (строка)

        Вокруг исправлений вставляются тэги '<span class="correction">' и '</span>',
        чтобы исправление рендерилось на странице с другим форматированием.
        """
        ORTHO = ["graph", "hyphen", "space", "ortho", "translit", "misspell", "deriv", "infl", "num", "gender", "morph"]
        sentence = sentence.split()
        dictionary = dict()
        for word_num in range(len(sentence)):
            dictionary[word_num] = sentence[word_num]
        for el in remarks:
            corr_start, corr_end, corr, tag = el
            tags = [i.lower().strip() for i in tag.split(',')]
            if any(i in ORTHO for i in tags):
                r = range(corr_start-1, corr_end)
                dictionary[r[0]] = '<span class="correction">' + corr + '</span>'
                for i in r[1:]:
                    dictionary[i] = ''
        s = ' '.join(dictionary[i] for i in sorted(dictionary) if dictionary[i] != '')
        return s

    def save(self, **kwargs):
        """
        Сохраняет аннотацию.

        Аннотация сохраняется в базу данных.
        При сохранении аннотации запускаются make_correction и make_ortho_correction,
        которые генерируют исправленные версии предложений. Исправленные варианты
        сохраняются в базу данных.
        """
        if not self.owner:
            return
        super(Annotation, self).save()
        sent_obj, sent_text = self.document, self.document.text
        remarks = self.get_sent_annotations(self.document_id)
        sent_obj.correct = self.make_correction(sent_text, remarks)
        sent_obj.correct2 = self.make_ortho_correction(sent_text, remarks)
        sent_obj.save()

    def delete(self, **kwargs):
        """
        Удаляет аннотацию.

        Аннотация удаляется из базы данных данных.
        При удалении аннотации запускаются make_correction и make_ortho_correction,
        которые заново генерируют исправленные версии предложений.
        Исправленные варианты сохраняются в базу данных.
        """
        sent_obj, sent_text = self.document, self.document.text
        doc_id = self.document_id
        super(Annotation, self).delete()
        remarks = self.get_sent_annotations(doc_id)
        sent_obj.correct = self.make_correction(sent_text, remarks)
        sent_obj.correct2 = self.make_ortho_correction(sent_text, remarks)
        sent_obj.save()

    def as_json(self, user=None):
        d = {"id": self.guid,
             "document": self.document_id,
             "created": self.created.isoformat(),
             "updated": self.updated.isoformat(),
             "readonly": not self.can_edit(user),
             }

        d.update(json.loads(self.data))

        return d

    def check_fields(self, start, end, startOffset, endOffset, quote, sent):
        # print start, end, sent
        q_enc = quote.encode('utf-8')
        q_len = len(q_enc.split(' '))
        # print (q_enc.split(' ')[-1])
        if start != '':
            start = bold_regex.sub('', start)
            self.start = int(span_regex.search(start).group(1))
            if end == "":  # /span[], ''
                end = '/span['+str(self.start+q_len-1)+']'
                endOffset = len(q_enc.split(' ')[-1].decode('utf-8').strip(' ,:;!?.'))
                print (q_enc.split(' ')[-1]), endOffset
            else:  # /span[], /span[]
                end = bold_regex.sub('', end)
            self.end = int(span_regex.search(end).group(1))
        else:
            if end != '':
                end = bold_regex.sub('', end)
                self.end = int(span_regex.search(end).group(1))
                start = '/span['+str(self.end-q_len+1)+']'
                startOffset = 0
                self.start = int(span_regex.search(start).group(1))
            else:
                sent = Sentence.objects.get(id=sent).text.encode('utf-8')
                # print sent
                s = re.split(q_enc, sent)
                for i in s: print i
                part = len(re.split(q_enc, sent)[0].strip().split(' '))
                self.start = part + 1
                self.end = part + q_len
                start = '/span['+str(self.start)+']'
                startOffset = 0
                end = '/span['+str(self.end)+']'
                endOffset = len(q_enc.split(' ')[-1].decode('utf-8').strip(' ,:;!?.'))
                # print (q_enc.split(' ')[-1]), endOffset
        return start, end, startOffset, endOffset

    def update_from_json(self, new_data):
        d = json.loads(self.data)

        for k, v in new_data.items():  # Skip special fields that we maintain and are not editable.
            if k in ('document', 'id', 'created', 'updated', 'readonly'):
                continue

                # Put other fields into the data object.
            d[k] = v

        quote = d['quote']
        # print quote, len(d['quote'])
        start, end, startOffset, endOffset = d["ranges"][0]["start"], d["ranges"][0]["end"], d["ranges"][0]["startOffset"], d["ranges"][0]["endOffset"]
        start, end, startOffset, endOffset = self.check_fields(start, end, startOffset, endOffset, quote, self.document.id)
        d["ranges"][0]["start"] = start
        d["ranges"][0]["end"] = end
        d["ranges"][0]["startOffset"] = startOffset
        d["ranges"][0]["endOffset"] = endOffset
        self.data = json.dumps(d)
        # print self.data
        self.tag = ', '.join(d["tags"])
        # print self.start, self.end

    @staticmethod
    def as_list(qs=None, user=None):
        if qs is None:
            qs = Annotation.objects.all()
        return [
            obj.as_json(user=user)
            for obj in qs.order_by('-updated')
        ]

    def __unicode__(self):
        d = json.loads(self.data)["quote"]
        return self.document.doc_id.title + ' - ' + d


class Token(models.Model):
    """Stores a single token, related to :model:`annotator.Document` and :model:`annotator.Sentence`."""
    token = models.CharField(max_length=200, db_index=True)
    doc = models.ForeignKey(Document)
    sent = models.ForeignKey(Sentence)
    num = models.IntegerField()
    punctl = models.CharField(max_length=100)
    punctr = models.CharField(max_length=100)
    sent_pos = models.CharField(max_length=30)
    corr = models.BooleanField(default=False)

    def __unicode__(self):
        return self.token

    class Meta:
        verbose_name = _('token')
        verbose_name_plural = _('tokens')


class Morphology(models.Model):
    """Stores morphological data, related to :model:`annotator.Token`."""
    # stupid class name, will change it someday
    token = models.ForeignKey(Token)
    lem = models.CharField(max_length=200, db_index=True)
    lex = models.CharField(max_length=200, db_index=True)
    gram = models.CharField(max_length=200, db_index=True)

    def __unicode__(self):
        return self.lem + ' ' + self.lex + ' ' + self.gram

    class Meta:
        verbose_name = _('analysis')
        verbose_name_plural = _('analyses')