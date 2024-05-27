from rest_framework import serializers
from validator.models.causes import Causes
from validator.models.question import Question


class BaseQuestion(serializers.Serializer):
    MODE_CHOICES = Question.ModeChoices

    class Meta:
        ref_name = 'BaseQuestion'
        
    mode = serializers.ChoiceField(choices=MODE_CHOICES)
    
class QuestionTitleRequest(serializers.Serializer):
    class Meta:
        ref_name = 'QuestionTitleRequest'
        
    title = serializers.CharField(max_length=40)
    
class QuestionTagRequest(serializers.Serializer):
    class Meta:
        ref_name = 'QuestionTagRequest'
        
    tags = serializers.ListField(
        min_length=1,
        max_length=3,
        child=serializers.CharField(max_length=10))    

class QuestionRequest(BaseQuestion):
    class Meta:
        ref_name = 'QuestionRequest'

    title = serializers.CharField(max_length=40)
    question = serializers.CharField()
    tags = serializers.ListField(
        min_length=1,
        max_length=3,
        child=serializers.CharField(max_length=10))    
    
class QuestionResponse(BaseQuestion):
    class Meta:
        ref_name = 'QuestionResponse'
    
    id = serializers.UUIDField()
    title = serializers.CharField(max_length=40)
    question = serializers.CharField()
    created_at = serializers.DateTimeField()
    username = serializers.CharField()
    tags = serializers.ListField(child=serializers.CharField())    


class FieldValuesResponse(serializers.Serializer):
    class Meta:
        ref_name = 'FieldValues'

    pengguna = serializers.ListField(child=serializers.CharField())
    judul = serializers.ListField(child=serializers.CharField())
    topik = serializers.ListField(child=serializers.CharField())


class PaginatedQuestionResponse(serializers.Serializer):
    class Meta:
        ref_name = 'QuestionResponsePaginated'

    count = serializers.IntegerField(default=5)
    next = serializers.URLField(default="http://localhost:8000/api/v1/validator/?p=2")
    previous = serializers.URLField(default="http://localhost:8000/api/v1/validator/?p=1")
    results = QuestionResponse(many=True)


class BaseCauses(serializers.Serializer):
    MODE_CHOICES = Causes.ModeChoices

    class Meta:
        ref_name = 'BaseCauses'
        
    cause = serializers.CharField()
    

class CausesRequest(BaseCauses):
    class Meta:
        ref_name = 'CausesRequest'

    MODE_CHOICES = Causes.ModeChoices

    question_id = serializers.UUIDField()
    row = serializers.IntegerField()
    column = serializers.IntegerField()
    mode = serializers.ChoiceField(choices=MODE_CHOICES)


class CausesResponse(BaseCauses):
    class Meta:
        ref_name = 'CausesResponse'
    
    id = serializers.UUIDField()
    question_id = serializers.UUIDField()
    row = serializers.IntegerField()
    column = serializers.IntegerField()
    status = serializers.BooleanField()
