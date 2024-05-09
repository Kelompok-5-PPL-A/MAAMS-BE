from django.urls import path

from validator.views.question import (
    QuestionGet, QuestionPost, QuestionPatch, QuestionDelete
) 
from validator.views.causes import (
    CausesGet, CausesPost, CausesPut, ValidateView
)


app_name = 'validator'

urlpatterns = [
    # questions
    path('', QuestionGet.as_view({ "get": "get_all"}), name="get_question_list"),
    path('<uuid:pk>/', QuestionGet.as_view({ 'get': 'get' }), name="get_question"),
    path('recent/', QuestionGet.as_view({ 'get': 'get_recent' }), name="get_recent"),
    path('search/', QuestionGet.as_view({ 'get': 'get_matched' }), name="get_matched"),
    path('pengawasan/', QuestionGet.as_view({ 'get': 'get_privileged' }), name="get_question_list_pengawasan"),
    path('field-values/', QuestionGet.as_view({ 'get': 'get_field_values'}), name="get_question_field_values"),
    path('baru/', QuestionPost.as_view(), name="create_question"),
    path('ubah/<uuid:pk>/', QuestionPatch.as_view({'patch': 'patch_mode'}), name="patch_mode_question"),
    path('ubah/judul/<uuid:pk>/', QuestionPatch.as_view({'patch': 'patch_title'}), name="patch_title_question"),
    # causes
    path('hapus/<uuid:pk>/', QuestionDelete.as_view(), name="delete_question"),
    path('causes/', CausesPost.as_view(), name="create_causes"),
    path('causes/<uuid:question_id>/<uuid:pk>', CausesGet.as_view(), name="get_causes"),
    path('causes/update/<uuid:question_id>/<uuid:pk>/', CausesPut.as_view(), name="put_causes"),
    path('causes/validate/<uuid:question_id>/', ValidateView.as_view(), name="validate_causes"),
]
