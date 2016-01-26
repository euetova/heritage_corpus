from django.conf.urls import patterns, url

from annotator.views import Root, Index, Annot, Search, EditorView, EditorView2, mark, get_correction, handle_upload

urlpatterns = patterns('',
	# storage API
    url(r'^/$', Root.as_view(), name='annotator.root'),
    url(r'^/annotations$', Index.as_view(), name='annotator.index'),
    url(r'^/annotations/([\w\-]+)$', Annot.as_view(), name='annotator.annotation'),
    url(r'^/search$', Search.as_view(), name='annotation.search'),
    url(r'^/get_correction_by_id/(?P<doc_id>[\w\-]+)', get_correction),
    
    # public pages
    url(r'^/document/(?P<doc_id>[\w\-]+)/edit$', EditorView.as_view(), name='annotation.editor'),
    url(r'^/document/(?P<doc_id>[\w\-]+)/edittest$', EditorView2.as_view(), name='annotation.editor2'),
    (r'^/document/(?P<doc_id>[\w\-]+)/mark$', mark),
    (r'^/document/(?P<doc_id>[\w\-]+)/handle_upload$', handle_upload),
)

