from dajax.core import Dajax
import json
from dajaxice.decorators import dajaxice_register
from models import Sentence


@dajaxice_register
def loadcorrections(request, num):
    num = int(num[:-1])
    sent = Sentence.objects.get(pk=num)
    # print sent.correct
    dajax = Dajax()
    dajax.assign('#'+str(num)+'+','innerHTML', sent.correct)

    return dajax.json()


@dajaxice_register
def multiply(request, a, b):
    dajax = Dajax()
    result = int(a) * int(b)
    dajax.assign('#result','value',str(result))
    return dajax.json()


@dajaxice_register
def sayhello(request):
    return json.dumps({'message':'Hello World'})

