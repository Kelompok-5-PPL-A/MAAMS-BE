from typing import List
import openai
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from authentication.models import CustomUser
from validator.dataclasses.create_cause import CreateCauseDataClass
from validator.models import question
from validator.models.causes import Causes
from validator.services import question
from validator.exceptions import NotFoundRequestException, ForbiddenRequestException, InvalidSubmissionException
from validator.constants import ErrorMsg
import uuid


class CausesService:
    def api_call(self, prompt: str):
        openai.api_key = settings.OPENAI_API_KEY
        response = openai.Completion.create(
                model="gpt-3.5-turbo",
                prompt=prompt,
                max_tokens=1,  
                n=3,           
                temperature=0  
            )
        answer = response.choices[0].text.strip()

        return answer

    def validate(self, question_id: uuid) -> List[CreateCauseDataClass]:
        max_row = Causes.objects.filter(problem_id=question_id).order_by('-row').values_list('row', flat=True).first()
        causes = Causes.objects.filter(problem_id=question_id, row=max_row)
        problem = question.Question.objects.get(pk=question_id)
        updated_causes = []

        if all(cause.status for cause in causes):
            raise InvalidSubmissionException("No cause to validate")

        for cause in causes:
            if not cause.status:
                self._validate_cause(cause, max_row, question_id, problem)
            updated_causes.append(cause)
        
        return [
            CreateCauseDataClass(
                question_id=question_id,
                id=cause.id,
                row=cause.row,
                column=cause.column,
                mode=cause.mode,
                cause=cause.cause,
                status=cause.status
            )
            for cause in updated_causes
        ]

    @staticmethod
    def _validate_cause(cause, max_row, question_id, problem):
        if max_row == 1:
            prompt = f"Is '{cause.cause}' the cause of '{problem.question}'? Answer using True/False"
        else:
            prev_cause = Causes.objects.filter(problem_id=question_id, row=max_row-1, column=cause.column).first()
            prompt = f"Is '{cause.cause}' the cause of '{prev_cause.cause}'? Answer using True/False"

        if CausesService.api_call(prompt):
            cause.status = True
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
            status=cause.status
        )

    def get(self, user: CustomUser, question_id: uuid, pk: uuid) -> CreateCauseDataClass:
        try:
            cause = Causes.objects.get(pk=pk, problem_id = question_id)
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
            status=cause.status
        )
        

    def update(self, user: CustomUser, question_id: uuid, pk: uuid, cause: str) -> CreateCauseDataClass:
        try:
            causes = Causes.objects.get(problem_id = question_id, pk=pk)
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
            status=causes.status
        )
        