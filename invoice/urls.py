from django.urls import path
from .views import NonDigitizeList,ParseDocument,ParsedDocumentView,UpdateDocument,DigitizeDocument,UploadView,StatusCheck,DigitizeList

app_name = 'invoice'

urlpatterns = [
    path('upload/',UploadView.as_view(),name='upload_view'),
    path('status/<int:pk>/',StatusCheck.as_view(),name='status_view'),
    path('non-digitizelist/',NonDigitizeList.as_view(),name='non_digitize_list'),
    path('digitize-list/',DigitizeList.as_view(),name='digitized_list'),
    path('parse/<int:pk>/',ParseDocument.as_view(),name='parse_document'),
    path('view-parse-detail/<int:pk>/',ParsedDocumentView.as_view(),name='view_parse_document'),
    path('update-document/<int:pk>/',UpdateDocument.as_view(),name='update_document'),
    path('digitize-document/<int:pk>/',DigitizeDocument.as_view(),name='digitize_document')
]