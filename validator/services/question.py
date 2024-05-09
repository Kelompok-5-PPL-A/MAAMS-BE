from typing import List
import uuid
from datetime import (
    datetime, timedelta
)
from multiprocessing.managers import BaseManager

from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from authentication.models import CustomUser

from validator.enums import (
    QuestionType, HistoryType, FilterType
)
from validator.constants import ErrorMsg
from validator.dataclasses.field_values import FieldValuesDataClass
from validator.dataclasses.create_question import CreateQuestionDataClass 
from validator.exceptions import (
    NotFoundRequestException, ForbiddenRequestException, 
    InvalidTimeRangeRequestException, InvalidTagException,
    InvalidFiltersException, ValueNotUpdatedException
)
from validator.models.causes import Causes
from validator.models.question import Question
from validator.models.tag import Tag
from validator.serializers import Question


class QuestionService():
    
    def create(self, user: CustomUser, title:str, question: str, mode: str, tags: List[str]):
        if not tags:
            raise InvalidTagException(ErrorMsg.EMPTY_TAG)
        if len(tags) > 3:
            raise InvalidTagException(ErrorMsg.TOO_MANY_TAG)
        tags_object = []
        
        for tag_name in tags:
            if len(tag_name) > 10:
                raise InvalidTagException(ErrorMsg.TAG_NAME_TOO_LONG)
            try:
                tag = Tag.objects.get(name=tag_name)
            except Tag.DoesNotExist:
                tag = Tag.objects.create(name=tag_name)
            finally:
                tags_object.append(tag)
                
        question_object = Question.objects.create(user=user, title=title, 
                                                  question=question, mode=mode)

        for tag in tags_object:
            question_object.tags.add(tag)
        
        tags = [tag.name for tag in question_object.tags.all()]

        return CreateQuestionDataClass(
            username = question_object.user.username,
            id = question_object.id,
            title=question_object.title,
            question = question_object.question,
            created_at = question_object.created_at,
            mode = question_object.mode,
            tags=tags
        )
    
    def get(self, user:CustomUser, pk:uuid):
        try:
            question_object = Question.objects.get(pk=pk)
        except ObjectDoesNotExist:
            raise NotFoundRequestException(ErrorMsg.NOT_FOUND)
        
        user_id = question_object.user.uuid
        
        if question_object.mode == Question.ModeChoices.PRIBADI and user.uuid != user_id:
            raise ForbiddenRequestException(ErrorMsg.FORBIDDEN_GET)

        if question_object.mode == Question.ModeChoices.PENGAWASAN and not (user.is_staff or user.is_superuser or user.uuid == user_id):
            raise ForbiddenRequestException(ErrorMsg.FORBIDDEN_GET)
        
        response = self._make_question_response([question_object])

        return response[0]
    
    def get_all(self, user: CustomUser,time_range: str):
        """
        Returns a list of  all questions corresponding to a specified user.
        """

        today_datetime = datetime.now()
        last_week_datetime = today_datetime - timedelta(days=7)
        
        # get all publicly available questions of mode "PENGAWASAN", depending on time range
        match time_range:
            case HistoryType.LAST_WEEK.value:
                questions = Question.objects.filter(user=user, created_at__range=[last_week_datetime, today_datetime]
                                                    ).order_by('-created_at')
            case HistoryType.OLDER.value:
                questions = Question.objects.filter(user=user, created_at__lt=last_week_datetime
                                                    ).order_by('-created_at')
                
        # get all questions filtered by user
        response = self._make_question_response(questions)

        return response
    
    def get_recent(self, user: CustomUser):
        recent_question = Question.objects.filter(user=user).order_by('-created_at').first()

        if (recent_question):
            response = self._make_question_response([recent_question])
            response = response[0]
        else:
            response = recent_question

        return response
    
    def get_privileged(self, q_filter: str, user: CustomUser, keyword: str):
        """
        Return a list for pengawasan questions by keyword and filter type for privileged users.
        """
        # allow only superuser/staff (admins) to access resource
        is_admin = user.is_superuser and user.is_staff
        if not is_admin:
            raise ForbiddenRequestException(ErrorMsg.FORBIDDEN_GET)
        
        if not q_filter: q_filter = 'semua'
        if not keyword: keyword = ''

        clause = self._resolve_filter_type(q_filter, keyword, is_admin)
        
        # query the questions with specified filters     
        mode = Q(mode=QuestionType.PENGAWASAN.value)       
        questions = Question.objects.filter(mode & clause).order_by('-created_at').distinct()

        # get all questions matching corresponding filters
        response = self._make_question_response(questions)

        return response
    
    def get_matched(self, q_filter: str, user: CustomUser, time_range: str, keyword: str):
        """
        Returns a list of matched questions corresponding to logged in user with specified filters.
        """
        is_admin = user.is_superuser and user.is_staff
        
        if not q_filter: q_filter = 'semua'
        if not keyword: keyword = ''

        today_datetime = datetime.now()
        last_week_datetime = today_datetime - timedelta(days=7)

        # append corresponding user to query
        user_filter = Q(user=user)

        clause = self._resolve_filter_type(q_filter, keyword, is_admin)

        time = self._resolve_time_range(time_range.lower(), today_datetime, last_week_datetime)

        # query the questions with specified filters            
        questions = Question.objects.filter(user_filter & clause & time).order_by('-created_at').distinct()

        # get all questions matching corresponding filters
        response = self._make_question_response(questions)

        return response

    def get_field_values(self, user: CustomUser) -> FieldValuesDataClass:
        """
        Returns all unique field values attached to available questions for search bar dropdown functionality.
        """
        is_admin = user.is_superuser and user.is_staff

        questions = Question.objects.all()

        values = {
            "judul": set(),
            "topik": set()
        }

        # extract usernames if user is admin to allow filtering by pengguna
        if is_admin: values['pengguna'] = set()
        
        for question in questions:
            if is_admin:
                values['pengguna'].add(question.user.username)
            values['judul'].add(question.title)
            # extract list of tags from question
            tags = [tag.name for tag in question.tags.all()]
            values['topik'].update(tags)

        response = FieldValuesDataClass(
            pengguna=[],
            judul=list(values['judul']), 
            topik=list(values['topik'])
        )

        if is_admin:
            response.pengguna=list(values['pengguna'])    

        return response 

    def update_question(self, user: CustomUser, pk: uuid, **fields):
        try:
            question = Question.objects.get(pk=pk)
        except Question.DoesNotExist:
            raise NotFoundRequestException(ErrorMsg.NOT_FOUND)
        
        if user.uuid != question.user.uuid:
            raise ForbiddenRequestException(ErrorMsg.FORBIDDEN_UPDATE)
        
        updated = False
        
        for field, new_value in fields.items():
            if getattr(question, field) != new_value:
                setattr(question, field, new_value)
                updated = True
        question.save()
            
        if not updated:
            raise ValueNotUpdatedException(ErrorMsg.VALUE_NOT_UPDATED)

        tags = [tag.name for tag in question.tags.all()]
        return CreateQuestionDataClass(
            username=question.user.username,
            id=question.id,
            title=question.title,
            question=question.question,
            created_at=question.created_at,
            mode=question.mode,
            tags=tags
        )
        
    def delete(self, user:CustomUser, pk:uuid):
        try:
            question_object = Question.objects.get(pk=pk)
        except ObjectDoesNotExist:
            raise NotFoundRequestException(ErrorMsg.NOT_FOUND)
        
        user_id = question_object.user.uuid

        if user.uuid != user_id:
            raise ForbiddenRequestException(ErrorMsg.FORBIDDEN_DELETE)
        
        tags = [tag.name for tag in question_object.tags.all()]
        question_data = CreateQuestionDataClass(
            username = question_object.user.username,
            id = question_object.id,
            title=question_object.title,
            question = question_object.question,
            created_at = question_object.created_at,
            mode = question_object.mode,
            tags=tags
        )
        related_causes = Causes.objects.filter(problem=question_object)
        related_causes.delete()
        question_object.delete()
        
        return question_data 
    
    """
    Utility functions.
    """
    def _make_question_response(self, questions) -> list:
        response = []
        if len(questions) == 0:
            return response
        for question in questions:
            tags = [tag.name for tag in question.tags.all()]
            item = CreateQuestionDataClass(
                username = question.user.username,
                id = question.id,
                title=question.title,
                question = question.question,
                created_at = question.created_at,
                mode = question.mode,
                tags=tags
            )
            response.append(item)
            
        return response
    
    def _resolve_filter_type(self, filter: str, keyword: str, is_admin: bool) -> Q:
        """
        Returns where clause for questions with specified filters/keywords.
        Only allow superusers/admin to filter by user.
        """
        match filter.lower():
            case FilterType.PENGGUNA.value:
                clause = (Q(user__username__icontains=keyword) | 
                          Q(user__first_name__icontains=keyword) | 
                          Q(user__last_name__icontains=keyword))
            case FilterType.JUDUL.value:
                clause = (Q(title__icontains=keyword) |
                          Q(question__icontains=keyword))
            case FilterType.TOPIK.value:
                clause = Q(tags__name__icontains=keyword)
            case FilterType.SEMUA.value:
                clause = (Q(title__icontains=keyword) |
                          Q(question__icontains=keyword) |
                          Q(tags__name__icontains=keyword))
                if is_admin:
                    clause |= Q(user__username__icontains=keyword)
            case _:
                raise InvalidFiltersException(ErrorMsg.INVALID_FILTERS)
        
        return clause
    
    def _resolve_time_range(self, time_range: str, today_datetime: datetime, last_week_datetime: datetime) -> Q:
        """
        Returns where clause for questions with specified time range.
        """
        match time_range.lower():
            case HistoryType.LAST_WEEK.value:
                time = Q(created_at__range=[last_week_datetime, today_datetime])
            case HistoryType.OLDER.value:
                time = Q(created_at__lt=last_week_datetime)
            case _:
                raise InvalidTimeRangeRequestException(ErrorMsg.INVALID_TIME_RANGE)
        
        return time
