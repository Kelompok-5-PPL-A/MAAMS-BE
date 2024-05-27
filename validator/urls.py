from django.urls import path

from validator.views.question import (
    QuestionGet, QuestionPost, QuestionPatch, QuestionDelete
) 
from validator.views.causes import (
    CausesGet, CausesPost, CausesPatch, ValidateView
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
    path('ubah/tags/<uuid:pk>/', QuestionPatch.as_view({'patch': 'patch_tags'}), name="patch_tags_question"),
    # causes
    path('hapus/<uuid:pk>/', QuestionDelete.as_view(), name="delete_question"),
    # causes
    path('causes/', CausesPost.as_view(), name="create_causes"),
    path('causes/<uuid:question_id>/', CausesGet.as_view({ 'get': 'get_list' }), name="get_causes_list"),
    path('causes/<uuid:question_id>/<uuid:pk>', CausesGet.as_view({ 'get': 'get' }), name="get_causes"),
    path('causes/patch/<uuid:question_id>/<uuid:pk>/', CausesPatch.as_view({'patch': 'patch_cause'}), name="patch_causes"),
    path('causes/validate/<uuid:question_id>/', ValidateView.as_view(), name="validate_causes"),
]
