from datetime import datetime
import json
import uuid

from django.urls import reverse

from rest_framework import status
from rest_framework.test import APITestCase

from authentication.models import CustomUser
from validator.enums import QuestionType
from validator.models.question import Question
from validator.models.causes import Causes
from validator.models.tag import Tag
from validator.serializers import (
    QuestionRequest, BaseQuestion
)

from django.core.exceptions import ObjectDoesNotExist

class QuestionViewTest(APITestCase):
    def setUp(self):
        """
        Set Up objects
        """
        self.question_uuid = uuid.uuid4()
        self.question_uuid2 = uuid.uuid4()
        self.question_uuid_super = uuid.uuid4()
        self.question_uuid_super2 = uuid.uuid4()
        
        self.user1 = CustomUser(
            username="test-username",
            email="test@email.com",
            is_superuser=True,
            is_staff=True 
        )
        self.user_uuid1 = self.user1.uuid
        self.user1.set_password('test-password')
        self.user1.save()

        self.user2 = CustomUser(
            username="test-username2",
            email="test2@email.com"
        )
        self.user_uuid2 = self.user2.uuid
        self.user2.set_password('test-password')
        self.user2.save()
        
        # valid data
        self.valid_data = {
            'title': 'Question 1',
            'question': 'Test question', 
            'mode': Question.ModeChoices.PRIBADI,
            'tags': ['economy', 'analysis']
        }
        self.valid_data_put = {'id': self.question_uuid, 'mode': Question.ModeChoices.PENGAWASAN}

        # invalid data for post
        self.invalid_data_missing = {'question': 'Test question missing', 'mode': ''}
        self.invalid_data = {'question': 'Test question invalid', 'mode': 'invalid'}
        
        # invalid data for put
        self.invalid_data_put = {'id': self.question_uuid, 'mode': 'invalid'}
        self.invalid_data_put_missing = {'id': self.question_uuid, 'mode': ''}
        self.invalid_data_put_user = {'id': self.question_uuid2, 'mode': Question.ModeChoices.PENGAWASAN}
        
        # urls
        self.post_url = 'validator:create_question'
        self.get_url = 'validator:get_question'
        self.get_all = 'validator:get_question_list'
        self.get_pengawasan = 'validator:get_question_list_pengawasan'
        self.put_url = 'validator:put_question'
        self.delete_url = 'validator:delete_question'
        self.get_matched = 'validator:get_matched'
        self.get_recent = 'validator:get_recent'

        """
        Create some tags
        """
        tag1 = Tag.objects.create(name="tag1")
        tag2 = Tag.objects.create(name="tag2")

        """
        Question created by user 1
        """
        self.question1 = Question.objects.create(
            user=self.user1,
            id=self.question_uuid, 
            title='pertanyaan 1',
            question='pertanyaan 1',
            mode=Question.ModeChoices.PRIBADI
        )
        self.question1.tags.add(tag1, tag2)
                
        self.causes_uuid = uuid.uuid4()
        Causes.objects.create(
            problem=self.question1,
            id=self.causes_uuid,
            row=1,
            column=1,
            mode=Causes.ModeChoices.PRIBADI,
            cause='cause',
            status=False
        )
        
        """
        Question created by user 2
        """
        self.question2 = Question.objects.create(
            user=self.user2,
            id=self.question_uuid2, 
            question='pertanyaan 2',
            title='pertanyaan 2',
            mode=Question.ModeChoices.PRIBADI
        )
        self.question2.tags.add(tag2)
                
        """
        Supervised Questions
        """
        self.question_super1 = Question.objects.create(
            user=self.user1,
            id=self.question_uuid_super, 
            title='pertanyaan supervised 1',
            question='pertanyaan supervised',
            mode=Question.ModeChoices.PENGAWASAN
        )
        self.question_super1.tags.add(tag1)
        
        self.question_super2 = Question.objects.create(
            user=self.user2,
            id=self.question_uuid_super2, 
            title='pertanyaan supervised 2',
            question='pertanyaan supervised',
            mode=Question.ModeChoices.PENGAWASAN
        )
        self.question_super2.tags.add(tag2)
        
        """
        User login
        """
        self.url_login = reverse('authentication:login')
        self.content_type_login = 'application/json'
        self.valid_credentials_login = {
            'username': 'test-username',
            'password': 'test-password'
        }
        
        response_login = self.client.post(
            self.url_login,
            data=json.dumps(self.valid_credentials_login),
            content_type=self.content_type_login,
        )
        
        access_token = response_login.data['access_token']  # Extracting access token from login response
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
    def test_get_question(self):
        url = reverse(self.get_url, kwargs={'pk': self.question_uuid})
        response = self.client.get(url)
        question = Question.objects.get(id=self.question_uuid)
        
        causes_count = Causes.objects.filter(problem_id=self.question_uuid).count()
        self.assertEqual(causes_count, 1)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], str(question.id))
        
    def test_get_non_existing_question(self):
        non_existing_pk = uuid.uuid4()
        url = reverse(self.get_url, kwargs={'pk': non_existing_pk})
        response = self.client.get(url)
        
        self.assertEqual(response.data['detail'], "Analisis tidak ditemukan")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
    def test_get_forbidden(self):
        url = reverse(self.get_url, kwargs={'pk': self.question_uuid2})
        response = self.client.get(url)
        
        self.assertEqual(response.data['detail'], "Pengguna tidak diizinkan untuk melihat analisis ini.")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
    def test_get_supervised_question(self):
        url = reverse(self.get_url, kwargs={'pk': self.question_uuid_super2})
        response = self.client.get(url)
        question = Question.objects.get(id=self.question_uuid_super2)
                
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], str(question.id)) 
        
    def test_post_question(self):
        url = reverse(self.post_url)
        response = self.client.post(url, self.valid_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['username'], 'test-username')
        self.assertEqual(Question.objects.get(id=response.data['id']).question, 'Test question')
    
    def test_post_question_missing_value(self):
        url = reverse(self.post_url)
        response = self.client.post(url, self.invalid_data_missing, format='json')
        serializer = QuestionRequest(data=self.invalid_data)
        
        self.assertFalse(serializer.is_valid())
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
    def test_post_question_invalid_value(self):
        url = reverse(self.post_url)
        response = self.client.post(url, self.invalid_data, format='json')
        
        serializer = QuestionRequest(data=self.invalid_data)
        
        self.assertFalse(serializer.is_valid())
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_put_question(self):
        url = reverse(self.put_url, kwargs={'pk': self.question_uuid})
        response = self.client.put(url, self.valid_data_put, format='json')
        
        updated_question = Question.objects.get(pk=self.question_uuid)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(updated_question.mode, Question.ModeChoices.PENGAWASAN)
        
    def test_put_question_invalid_value(self):
        url = reverse(self.put_url, kwargs={'pk': self.question_uuid})
        response = self.client.put(url, self.invalid_data_put, format='json')
        
        serializer = BaseQuestion(data=self.invalid_data_put)
        
        self.assertFalse(serializer.is_valid())
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
    def test_put_question_missing_value(self):
        url = reverse(self.put_url, kwargs={'pk': self.question_uuid})
        response = self.client.put(url, self.invalid_data_put_missing, format='json')
        
        serializer = BaseQuestion(data=self.invalid_data_put_missing)

        self.assertFalse(serializer.is_valid())
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
    def test_put_nonexisting_question(self):
        non_existing_pk = uuid.uuid4()
        url = reverse(self.put_url, kwargs={'pk': non_existing_pk})
        response = self.client.put(url, self.valid_data_put, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_put_forbidden(self):
        url = reverse(self.put_url, kwargs={'pk': self.question_uuid2})
        response = self.client.put(url, self.valid_data_put, format='json')
        
        self.assertEqual(response.data['detail'], "Pengguna tidak diizinkan untuk mengubah analisis ini.")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
    def test_delete_question(self):
        url = reverse(self.delete_url, kwargs={'pk': self.question_uuid})
        response = self.client.delete(url)

        self.assertEqual(response.data['message'], "Analisis berhasil dihapus")
        self.assertEqual(uuid.UUID(response.data['deleted_question']['id']), self.question_uuid)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        with self.assertRaises(ObjectDoesNotExist):
            Question.objects.get(pk=self.question_uuid)
        
        causes_count = Causes.objects.filter(problem_id=self.question_uuid).count()
        self.assertEqual(causes_count, 0)
        
    def test_delete_question_not_found(self):
        non_existing_pk = uuid.uuid4()
        url = reverse(self.delete_url, kwargs={'pk': non_existing_pk})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['detail'], "Analisis tidak ditemukan")
        
    def test_delete_question_forbidden(self):
        url = reverse(self.delete_url, kwargs={'pk': self.question_uuid2})
        response = self.client.delete(url)
                
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data['detail'], "Pengguna tidak diizinkan untuk menghapus analisis ini.")

    def test_get_supervised_question_fail(self):
        valid_credentials_login2 = {
            'username': 'test-username2',
            'password': 'test-password'
        }
        
        response_login = self.client.post(
            self.url_login,
            data=json.dumps(valid_credentials_login2),
            content_type=self.content_type_login,
        )
        
        access_token = response_login.data['access_token']
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        url = reverse(self.get_url, kwargs={'pk': self.question_uuid_super})
        response = self.client.get(url)
                
        self.assertEqual(response.data['detail'], "Pengguna tidak diizinkan untuk melihat analisis ini.")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_recent_question(self):
        Question.objects.all().delete()
        url_post = reverse(self.post_url)
        
        response__old_post = self.client.post(url_post, self.valid_data, format='json')
        old_post_id = Question.objects.get(id=response__old_post.data['id']).id
        
        response__new_post = self.client.post(url_post, self.valid_data, format='json')
        new_post_id = Question.objects.get(id=response__new_post.data['id']).id
        
        url_recent = reverse(self.get_recent)
        response_recent = self.client.get(url_recent)
        
        self.assertEqual(response_recent.status_code, status.HTTP_200_OK)
        self.assertEqual(response_recent.data['id'], str(new_post_id))
        self.assertNotEqual(response_recent.data['id'], str(old_post_id))
        
    def test_get_recent_none(self):
        Question.objects.all().delete()
        url_recent = reverse(self.get_recent)
        response_recent = self.client.get(url_recent)
        
        self.assertEqual(response_recent.status_code, status.HTTP_200_OK)
        self.assertEqual(response_recent.data['id'], None)

    def test_get_pengawasan_last_week(self):
        # set user as superuser (for admin testing purposes)
        self.user1.is_superuser = True
        self.user1.is_staff = True
        self.user1.save()

        url = reverse(self.get_pengawasan)
        response = self.client.get(url + '?time_range=last_week')
        questions = Question.objects.filter(mode=QuestionType.PENGAWASAN.value)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], len(questions))

    def test_get_pengawasan_older(self):
        # reset questions
        Question.objects.all().delete()

        url = reverse(self.get_pengawasan)
        response = self.client.get(url + '?time_range=older')
        questions = Question.objects.filter(mode=QuestionType.PENGAWASAN.value)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], len(questions))

    def test_get_pengawasan_questions_forbidden(self):
        # reset user status
        self.user1.is_superuser = False
        self.user1.is_staff = False
        self.user1.save()

        url = reverse(self.get_pengawasan)
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data['detail'], "Pengguna tidak diizinkan untuk melihat analisis ini.")
    
    def test_get_pengawasan_no_keyword(self):
        # set user as superuser (for admin testing purposes)
        self.user1.is_superuser = True
        self.user1.is_staff = True
        self.user1.save()
        
        url = reverse(self.get_pengawasan)
        response = self.client.get(url + '?time_range=last_week')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('count', response.data)
        self.assertIn('results', response.data)
    
    def test_get_pengawasan_invalid_time_range(self):
        url = reverse(self.get_pengawasan)
        response = self.client.get(url + '?keyword=test&time_range=invalid_format')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['detail'], "Invalid time range format.")
    
    def test_get_pengawasan_unauthorized_access(self):
        # Remove authentication
        self.client.credentials()
        url = reverse(self.get_pengawasan)
        response = self.client.get(url + '?keyword=test&time_range=last_week')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data['detail'], "Authentication credentials were not provided.")
    
    def test_get_pengawasan_empty_keyword(self):
        # set user as superuser (for admin testing purposes)
        self.user1.is_superuser = True
        self.user1.is_staff = True
        self.user1.save()
        
        url = reverse(self.get_pengawasan)
        response = self.client.get(url + '?keyword=&time_range=last_week')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('count', response.data)
        self.assertIn('results', response.data)

        # reset user status
        self.user1.is_superuser = False
        self.user1.is_staff = False
        self.user1.save()
        
    def test_get_all_questions_last_week(self):
        Question.objects.all().delete()
        url = reverse(self.get_all)
        response = self.client.get(url + '?time_range=last_week')
        questions = Question.objects.filter(user=self.user1)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], len(questions))

    def test_get_all_questions_older(self):
        Question.objects.all().delete()
        url = reverse(self.get_all)
        response = self.client.get(url + '?time_range=older')
        questions = Question.objects.filter(user=self.user1)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], len(questions))
        
    def test_get_matched(self):
        url = reverse(self.get_matched)
        response = self.client.get(url + '?keyword=test&time_range=last_week')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('count', response.data)
        self.assertIn('results', response.data)

    def test_get_matched_no_keyword(self):
        url = reverse(self.get_matched)
        response = self.client.get(url + '?time_range=last_week')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('count', response.data)
        self.assertIn('results', response.data)

    def test_get_matched_invalid_time_range(self):
        url = reverse(self.get_matched)
        response = self.client.get(url + '?keyword=test&time_range=invalid_format')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['detail'], "Invalid time range format.")

    def test_get_matched_unauthorized_access(self):
        # Remove authentication
        self.client.credentials()
        url = reverse(self.get_matched)
        response = self.client.get(url + '?keyword=test&time_range=last_week')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data['detail'], "Authentication credentials were not provided.")
   
    def test_get_matched_empty_keyword(self):
        url = reverse(self.get_matched)
        response = self.client.get(url + '?keyword=&time_range=last_week')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('count', response.data)
        self.assertIn('results', response.data)

    def test_get_matched_older_questions(self):
        url = reverse(self.get_matched)
        response = self.client.get(url + '?keyword=test&time_range=older')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('count', response.data)
        self.assertIn('results', response.data)