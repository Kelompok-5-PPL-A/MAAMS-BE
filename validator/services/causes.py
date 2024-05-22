from typing import List
from groq import Groq
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from authentication.models import CustomUser
from validator.dataclasses.create_cause import CreateCauseDataClass
from validator.models import question
from validator.models.causes import Causes
from validator.services import question
from validator.exceptions import NotFoundRequestException, ForbiddenRequestException, AIServiceErrorException
from validator.constants import ErrorMsg
import uuid
import requests

class CausesService:
    def api_call(self, system_message: str, user_prompt: str) -> str:
        client = Groq(api_key=settings.GROQ_API_KEY)
        
        try:
            chat_completion = client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": system_message,
                    },
                    {
                        "role": "user",
                        "content": user_prompt
                    }
                ],
                model="llama3-8b-8192",
                max_tokens=5
            )
            
            answer = chat_completion.choices[0].message.content
            print(answer)
        except requests.exceptions.RequestException:
            raise AIServiceErrorException(ErrorMsg.AI_SERVICE_ERROR)
        
        if answer.strip().lower().__contains__('true'):
            return True
        elif answer.strip().lower().__contains__('false'):
            return False
    
    def validate(self, question_id: uuid):
        max_row = Causes.objects.filter(problem_id=question_id).order_by('-row').values_list('row', flat=True).first()
        causes = Causes.objects.filter(problem_id=question_id, row=max_row)
        problem = question.Question.objects.get(pk=question_id)

        for cause in causes:
            if cause.status:
                continue
            
            user_prompt = ""
            system_message = "You are an AI model. You are asked to determine whether the given cause is the cause of the given problem."
            
            if max_row == 1:
                user_prompt = f"Is '{cause.cause}' the cause of this question: '{problem.question}'? Answer only with True/False"
                
            else:
                prev_cause = Causes.objects.filter(problem_id=question_id, row=max_row-1, column=cause.column).first()
                user_prompt = f"Is '{cause.cause}' the cause of '{prev_cause.cause}'? Answer only with True/False"
                
            if self.api_call(self=self, system_message=system_message, user_prompt=user_prompt):
                cause.status = True
                if max_row > 1 and CausesService.validate_root(self=self, cause=cause, problem=problem):
                    cause.root_status = True
                
                cause.save()

    def validate_root(self, cause: Causes, problem: question.Question):
        root_check_user_prompt = f"Is '{cause.cause}' a root cause of {problem.question}? Answer only with True/False."
        root_check_system_message = "You are an AI model. You are asked to determine whether the given cause is a root cause of the given problem."
        
        if CausesService.api_call(self=self, system_message=root_check_system_message, user_prompt=root_check_user_prompt):
            cause.root_status = True
            cause.save()
        
    def create(self, question_id: uuid, cause: str, row: int, column: int, mode: str) -> CreateCauseDataClass:
        cause = Causes.objects.create(
            problem=question.Question.objects.get(pk=question_id),
            row=row,
            column=column,
            mode=mode,
            cause=cause
        )
        return CreateCauseDataClass(
            question_id=cause.problem.id,
            id=cause.id,
            row=cause.row,
            column=cause.column,
            mode=cause.mode,
            cause=cause.cause,
            status=cause.status,
            root_status=cause.root_status
        )

    def get(self, user: CustomUser, question_id: uuid, pk: uuid) -> CreateCauseDataClass:
        try:
            cause = Causes.objects.get(pk=pk, problem_id=question_id)
            cause_user_uuid = question.Question.objects.get(pk=question_id).user.uuid
        except ObjectDoesNotExist:
            raise NotFoundRequestException(ErrorMsg.CAUSE_NOT_FOUND)

        if user.uuid != cause_user_uuid and cause.mode == Causes.ModeChoices.PRIBADI:
            raise ForbiddenRequestException(ErrorMsg.FORBIDDEN_GET)

        if cause.mode == Causes.ModeChoices.PENGAWASAN and not user.is_staff and user.uuid != cause_user_uuid:
            raise ForbiddenRequestException(ErrorMsg.FORBIDDEN_GET)

        return CreateCauseDataClass(
            question_id=question_id,
            id=cause.id,
            row=cause.row,
            column=cause.column,
            mode=cause.mode,
            cause=cause.cause,
            status=cause.status,
            root_status=cause.root_status
        )

    def get_list(self, user: CustomUser, question_id: uuid) -> List[CreateCauseDataClass]:
        try:
            cause = Causes.objects.filter(problem_id=question_id)
            current_question = question.Question.objects.get(pk=question_id)
            cause_user_uuid = current_question.user.uuid
        except ObjectDoesNotExist:
            raise NotFoundRequestException(ErrorMsg.CAUSE_NOT_FOUND)

        if user.uuid != cause_user_uuid and current_question.mode == question.Question.ModeChoices.PRIBADI:
            raise ForbiddenRequestException(ErrorMsg.FORBIDDEN_GET)

        if not user.is_staff and user.uuid != cause_user_uuid and current_question.mode == question.Question.ModeChoices.PENGAWASAN:
            raise ForbiddenRequestException(ErrorMsg.FORBIDDEN_GET)

        return [
            CreateCauseDataClass(
                question_id=question_id,
                id=cause.id,
                row=cause.row,
                column=cause.column,
                mode=cause.mode,
                cause=cause.cause,
                status=cause.status,
                root_status=cause.root_status
            )
            for cause in cause
        ]

    def patch_cause(self, user: CustomUser, question_id: uuid, pk: uuid, cause: str) -> CreateCauseDataClass:
        try:
            causes = Causes.objects.get(problem_id=question_id, pk=pk)
            causes.cause = cause
            causes.save()
        except ObjectDoesNotExist:
            raise NotFoundRequestException(ErrorMsg.CAUSE_NOT_FOUND)

        if user.uuid != question.Question.objects.get(pk=question_id).user.uuid:
            raise ForbiddenRequestException(ErrorMsg.FORBIDDEN_UPDATE)

        return CreateCauseDataClass(
            question_id=question_id,
            id=causes.id,
            row=causes.row,
            column=causes.column,
            mode=causes.mode,
            cause=causes.cause,
            status=causes.status,
            root_status=causes.root_status
        )
        