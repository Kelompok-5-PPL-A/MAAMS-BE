from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from unittest.mock import patch
from validator.models.causes import Causes
from validator.models.question import Question
from validator.services.causes import CausesService
from authentication.models import CustomUser
from validator.serializers import CausesResponse, CausesRequest, BaseCauses
import uuid
import json

class CausesViewTest(APITestCase):
    def setUp(self):
        """
        Set Up objects
        """
        self.user1 = CustomUser.objects.create(
            username="test-username",
            email="test@email.com"
        )
        self.user_uuid1 = self.user1.uuid
        self.user1.set_password('test-password')
        self.user1.save()


        self.user2 = CustomUser.objects.create(
            username="test-username2",
            email="test2@email.com"
        )
        self.user_uuid2 = self.user2.uuid
        self.user2.set_password('test-password')
        self.user2.save()

        self.question_uuid1 = uuid.uuid4()
        self.question_uuid2 = uuid.uuid4()

        self.question1 = Question.objects.create(
            user=self.user1,
            id=self.question_uuid1,
            question='pertanyaan',
            mode=Question.ModeChoices.PRIBADI
        )

        self.question2 = Question.objects.create(
            user=self.user2,
            id=self.question_uuid2,
            question='pertanyaan',
            mode=Question.ModeChoices.PRIBADI
        )

        self.causes_uuid = uuid.uuid4()
        self.causes_uuid2 = uuid.uuid4()

        self.causes1 = Causes.objects.create(
            problem=self.question1,
            id=self.causes_uuid,
            row=1,
            column=1,
            mode=Causes.ModeChoices.PRIBADI,
            cause='cause',
            status=False
        )

        self.causes2 = Causes.objects.create(
            problem=self.question2, 
            id=self.causes_uuid2,
            row=1,
            column=1,
            mode=Causes.ModeChoices.PENGAWASAN,
            cause='',
            status=False
        )

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

        access_token = response_login.data['access_token']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
    
        self.post_url = 'validator:create_causes'
        self.get_url = 'validator:get_causes'
        self.put_url = 'validator:put_causes'
        self.validate_url = 'validator:validate_causes'

    def test_create_cause_positive(self):
        self.valid_data = {
                           'question_id': self.question_uuid1, 
                           'cause': 'cause', 
                           'row': 1,
                           'column': 1,
                           'mode': Question.ModeChoices.PRIBADI
                           }
        url = reverse(self.post_url)
        response = self.client.post(url, self.valid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['cause'], 'cause')

    def test_create_cause_negative_missing_cause(self):
        self.invalid_data_missing_cause = {'problem': self.question_uuid1, 'row': 1, 'column': 1, 'mode': ''}
        response = self.client.post(self.post_url, self.invalid_data_missing_cause, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_get_cause_positive(self):
        url = reverse(self.get_url, kwargs={'question_id': self.question_uuid1,'pk': self.causes_uuid})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], str(self.causes_uuid))

    def test_get_cause_negative_non_existing_cause(self):
        non_existing_pk = uuid.uuid4()
        url = reverse(self.get_url, kwargs={'question_id': str(non_existing_pk), 'pk': str(non_existing_pk)})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_cause_forbidden(self):
        url = reverse(self.get_url, kwargs={'question_id': self.question_uuid2,'pk': self.causes_uuid2})
        response = self.client.get(url)
                
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data['detail'], "Pengguna tidak diizinkan untuk menghapus analisis ini.")
    
    def test_put_cause_positive(self):
        self.valid_data = {'question_id': str(self.question_uuid1), 'id':self.causes_uuid, 'row': 2, 'column': 2, 'mode': Causes.ModeChoices.PRIBADI, 'cause': 'Updated Cause'}

        url = reverse(self.put_url, kwargs={'question_id': str(self.question_uuid1), 'pk': str(self.causes_uuid)})
        data = {'question_id': self.question_uuid1, 'id':self.causes_uuid, 'cause': 'Updated Cause'}
        response = self.client.put(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_put_cause_forbidden(self):
        self.valid_data = {'question_id': str(self.question_uuid2), 'id':self.causes_uuid2, 'row': 2, 'column': 2, 'mode': Causes.ModeChoices.PENGAWASAN, 'cause': 'Updated Cause'}

        url = reverse(self.put_url, kwargs={'question_id': str(self.question_uuid2), 'pk': str(self.causes_uuid2)})
        data = {'question_id': self.question_uuid2, 'id':self.causes_uuid2, 'cause': 'Updated Cause'}
        response = self.client.put(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_put_cause_invalid_data(self):
        url = reverse(self.put_url, kwargs={'question_id': str(self.question_uuid1), 'pk': self.causes_uuid})
        self.invalid_data_put = {'problem': self.question_uuid1, 'row': 1, 'column': 1, 'mode': ''}
        response = self.client.put(url, self.invalid_data_put, format='json')
        
        serializer = BaseCauses(data=self.invalid_data_put)
        
        self.assertFalse(serializer.is_valid())
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


    def test_put_cause_missing_data(self):
        non_existing_pk = uuid.uuid4()
        url = reverse(self.put_url, kwargs={'question_id': str(non_existing_pk), 'pk': str(non_existing_pk)})
        self.invalid_data_put = {'cause': 'Updated cause'}
        response = self.client.put(url, self.invalid_data_put, format='json')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


    '''
    validator unittest section
    '''
    def test_rca_row_equal_1(self):
        with patch.object(CausesService, 'api_call', return_value=True):
            url = reverse(self.validate_url, kwargs={'question_id': self.question_uuid1})
            response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.causes1.refresh_from_db()

        self.assertTrue(self.causes1.status)

    def test_rca_row_greater_than_1(self):
        question_id = uuid.uuid4()
        question = Question.objects.create(pk=question_id, question='Test question')

        Causes.objects.create(problem=question, row=1, column=1, mode='PRIBADI', cause='Cause 1')
        cause2 = Causes.objects.create(problem=question, row=2, column=1, mode='PRIBADI', cause='Cause 1')

        with patch.object(CausesService, 'api_call', return_value=True):
            url = reverse(self.validate_url, kwargs={'question_id': question_id})
            response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        cause2.refresh_from_db()
        self.assertTrue(cause2.status)

    def test_rca_row_not_updated(self):
        Causes.objects.create(problem=Question.objects.get(pk=self.question_uuid1), row=2, column=1, mode='PRIBADI', cause='different cause')

        with patch.object(CausesService, 'api_call', return_value=False):
            url = reverse(self.validate_url, kwargs={'question_id': self.question_uuid1})
            response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(Causes.objects.get(problem=Question.objects.get(pk=self.question_uuid1), row=2).status)

    '''
    Admin Role Tests
    '''
    
    def test_get_cause_superuser_forbidden(self):
        self.superuser = CustomUser.objects.create_superuser('admin', 'admin@example.com', 'adminpassword')
        
        response_login = self.client.post(
            self.url_login,
            data=json.dumps({'username': 'admin', 'password': 'adminpassword'}),
            content_type=self.content_type_login,
        )
        
        access_token = response_login.data['access_token']
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')

        url = reverse(self.get_url, kwargs={'question_id': self.question_uuid1,'pk': self.causes_uuid})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_cause_superuser_positive(self):
        self.superuser = CustomUser.objects.create_superuser('admin', 'admin@example.com', 'adminpassword')
        
        response_login = self.client.post(
            self.url_login,
            data=json.dumps({'username': 'admin', 'password': 'adminpassword'}),
            content_type=self.content_type_login,
        )
        
        access_token = response_login.data['access_token']
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')

        url = reverse(self.get_url, kwargs={'question_id': self.question_uuid2,'pk': self.causes_uuid2})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)