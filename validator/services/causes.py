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
from validator.enums import (
    ValidationType
)
from validator.constants import FeedbackMsg

class CausesService:
    def api_call(self, system_message: str, user_prompt: str, validation_type:ValidationType) -> int:
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
                temperature=0.1,
                max_tokens=50,
                seed=42
            )
            
            answer = chat_completion.choices[0].message.content
        
        except requests.exceptions.RequestException:
            raise AIServiceErrorException(ErrorMsg.AI_SERVICE_ERROR)
        
        if validation_type in [ValidationType.NORMAL, ValidationType.ROOT]:
            if answer.lower().__contains__('true'):
                return 1
            elif answer.lower().__contains__('false'):
                return 0
        else:
            if answer.__contains__('1'):
                return 1
            elif answer.__contains__('2'):
                return 2
            elif answer.__contains__('3'):  
                return 3
    
    def validate(self, question_id: uuid):
        max_row = Causes.objects.filter(problem_id=question_id).order_by('-row').values_list('row', flat=True).first()
        causes = Causes.objects.filter(problem_id=question_id, row=max_row)
        problem = question.Question.objects.get(pk=question_id)

        for cause in causes:
            if cause.status:
                continue
            
            user_prompt = ""
            prev_cause = None
            system_message = "You are an AI model. You are asked to determine whether the given cause is the cause of the given problem."
            
            if max_row == 1:
                user_prompt = f"Is '{cause.cause}' the cause of this question: '{problem.question}'? Answer only with True/False"
                
            else:
                prev_cause = Causes.objects.filter(problem_id=question_id, row=max_row-1, column=cause.column).first()
                user_prompt = f"Is '{cause.cause}' the cause of '{prev_cause.cause}'? Answer only with True/False"
                
            if self.api_call(self=self, system_message=system_message, user_prompt=user_prompt, validation_type=ValidationType.NORMAL) == 1:
                cause.status = True
                cause.feedback = ""
                if max_row > 1:
                    CausesService.check_root_cause(self=self, cause=cause, problem=problem)

            else:
                CausesService.retrieve_feedback(self=self, cause=cause, problem=problem, prev_cause = prev_cause)
            
            cause.save()
    
    def check_root_cause(self, cause: Causes, problem: question.Question):
        root_check_user_prompt = f"Is the cause '{cause.cause}' the fundamental reason behind the problem '{problem.question}'? Answer only with True or False."
        root_check_system_message = (
            "You are an AI model. You are asked to determine whether the given cause is a root cause of the given problem. "
            "A root cause is the fundamental underlying reason for a problem, which, if addressed, would prevent recurrence of the problem. "
            "Not all direct causes are root causes; while direct causes contribute to the problem, root causes are the deepest level of causation. "
            "Your task is to distinguish between direct causes and root causes, identifying whether the given cause is indeed the fundamental issue driving the problem."
        )
        
        if CausesService.api_call(self=self, system_message=root_check_system_message, user_prompt=root_check_user_prompt, validation_type=ValidationType.ROOT) == 1:
            cause.root_status = True
    
    def retrieve_feedback(self, cause: Causes, problem: question.Question, prev_cause: None|Causes):
        retrieve_feedback_user_prompt = ""
        retrieve_feedback_system_message = ""
        
        if prev_cause:
            retrieve_feedback_user_prompt = (
                f"'{cause.cause}' is the FALSE cause for '{prev_cause.cause}'. "
                "Now determine if it is false because it is NOT THE CAUSE, because it is a POSITIVE OR NEUTRAL cause, or because it is SIMILAR TO THE PREVIOUS cause. "
                "Answer ONLY WITH '1' if it is NOT THE CAUSE,  "
                "ONLY WITH '2' if it is POSITIVE OR NEUTRAL, or "
                "ONLY WITH '3' if it is SIMILAR TO THE PREVIOUS cause."
            )
            retrieve_feedback_system_message = (
                "You are an AI model. You are asked to determine the relationship between the given causes. "
                "Please respond ONLY WITH '1' if the cause is NOT THE CAUSE of the previous cause, "
                "ONLY WITH '2' if the cause is POSITIVE OR NEUTRAL, or "
                "ONLY WITH '3' if the cause is SIMILAR TO THE PREVIOUS cause."
            )        
        else:
            retrieve_feedback_user_prompt = (
                f"'{cause.cause}' is the FALSE cause for this question '{problem.question}'. "
                "Now determine if it is false because it is NOT THE CAUSE or because it is a POSITIVE OR NEUTRAL CAUSE. "
                "Answer ONLY with '1' if it is NOT THE CAUSE, '2' if it is POSITIVE OR NEUTRAL."
            )
            retrieve_feedback_system_message = (
                "You are an AI model. You are asked to determine the relationship between problem and cause. "
                "Please respond ONLY WITH '1' if the cause is NOT THE CAUSE of the question, ONLY WITH '2' if the cause is positive or neutral"
            )
        
        feedback_type = CausesService.api_call(self=self, system_message=retrieve_feedback_system_message, user_prompt=retrieve_feedback_user_prompt, validation_type=ValidationType.FALSE)
            
        if feedback_type == 1 and prev_cause:
            cause.feedback = FeedbackMsg.FALSE_ROW_N_NOT_CAUSE.format(column='ABCDE'[cause.column], row=cause.row, prev_row=cause.row-1)
        elif feedback_type == 1:
            cause.feedback = FeedbackMsg.FALSE_ROW_1_NOT_CAUSE.format(column='ABCDE'[cause.column])
        elif feedback_type == 2:
            cause.feedback = FeedbackMsg.FALSE_ROW_N_POSITIVE_NEUTRAL.format(column='ABCDE'[cause.column], row=cause.row)     
        elif feedback_type == 3:
            cause.feedback = FeedbackMsg.FALSE_ROW_N_SIMILAR_PREVIOUS.format(column='ABCDE'[cause.column], row=cause.row) 
               
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
            root_status=cause.root_status,
            feedback = cause.feedback
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
            root_status=cause.root_status,
            feedback = cause.feedback
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
                root_status=cause.root_status,
                feedback = cause.feedback
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
            root_status=causes.root_status,
            feedback = causes.feedback
        )
        