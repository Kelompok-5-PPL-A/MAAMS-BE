from validator.models.question import Question
from authentication.models import CustomUser
import uuid
from django.core.exceptions import ObjectDoesNotExist
from validator.exceptions import NotFoundRequestException

class QuestionService():
    def create(user: CustomUser, question: str, mode: str):
        question = Question.objects.create(user=user, question=question, mode=mode)
        return question
    
    def get(user:CustomUser, pk:uuid):
        try:
            question = Question.objects.get(pk=pk)
        except ObjectDoesNotExist:
            raise NotFoundRequestException("Analisis tidak ditemukan")
        
        # TODO: Check user and mode
        # if user not the same as the creator, check if the user an admin
        # if admin, check if mode == pengawasan
        # raise ForbiddenRequestException("User not permitted to view this resource")
        return question

    def update_mode(user:CustomUser, mode:str, pk:uuid):
        try:
            question = Question.objects.get(pk=pk)
        except ObjectDoesNotExist:
            raise NotFoundRequestException("Analisis tidak ditemukan")
        
        # TODO: Check user
        # raise ForbiddenRequestException("User not permitted to update this resource")
        question.mode = mode
        question.save()
        
        return question