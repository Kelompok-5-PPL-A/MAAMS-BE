from django.test import TestCase
from unittest.mock import patch, Mock
from django.conf import settings
from validator.services.causes import CausesService
from validator.models.causes import Causes
from validator.models.question import Question
import uuid
from requests.exceptions import RequestException
from validator.exceptions import AIServiceErrorException

class CausesServiceTest(TestCase):
    @patch('validator.services.causes.Groq')
    def test_api_call_positive(self, mock_groq):
        mock_client = Mock()
        mock_chat_completion = Mock()
        mock_chat_completion.choices = [Mock(message=Mock(content='True'))]
        mock_client.chat.completions.create.return_value = mock_chat_completion
        mock_groq.return_value = mock_client

        service = CausesService()
        prompt = "Is 'Example cause' the cause of 'Example problem'? Answer using only True/False"
        response = service.api_call(prompt)

        self.assertTrue(response)
        mock_client.chat.completions.create.assert_called_once_with(
            messages=[
                {
                    "role": "system",
                    "content": "You are an AI model. You are asked to determine whether the given cause is the cause of the given problem.",
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            model="llama3-8b-8192",
        )

    @patch('validator.services.causes.Groq')
    def test_api_call_returns_false(self, mock_groq):
        mock_client = Mock()
        mock_chat_completion = Mock()
        mock_chat_completion.choices = [Mock(message=Mock(content='False this is not the cause'))]
        mock_client.chat.completions.create.return_value = mock_chat_completion
        mock_groq.return_value = mock_client

        service = CausesService()
        prompt = "Is 'Example cause' the cause of 'Example problem'? Answer using only True/False"
        response = service.api_call(prompt)

        self.assertFalse(response)
        mock_client.chat.completions.create.assert_called_once_with(
            messages=[
                {
                    "role": "system",
                    "content": "You are an AI model. You are asked to determine whether the given cause is the cause of the given problem.",
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            model="llama3-8b-8192",
        )

    @patch('validator.services.causes.Groq')
    def test_api_call_request_exception(self, mock_groq):
        mock_client = Mock()
        mock_client.chat.completions.create.side_effect = RequestException("Network error")
        mock_groq.return_value = mock_client

        service = CausesService()
        prompt = "Is 'Example cause' the cause of 'Example problem'? Answer using only True/False"

        with self.assertRaises(AIServiceErrorException) as context:
            service.api_call(prompt)

        mock_client.chat.completions.create.assert_called_once_with(
            messages=[
                {
                    "role": "system",
                    "content": "You are an AI model. You are asked to determine whether the given cause is the cause of the given problem.",
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            model="llama3-8b-8192",
        )

        self.assertTrue("Failed to call the AI service." in str(context.exception))

    @patch('validator.services.causes.Groq')
    def test_api_call_negative(self, mock_groq):
        mock_client = Mock()
        mock_client.chat.completions.create.side_effect = Exception("API call failed")
        mock_groq.return_value = mock_client

        service = CausesService()
        prompt = "test prompt"
        with self.assertRaises(Exception):
            service.api_call(prompt)

    @patch('validator.services.causes.Groq')
    def test_api_call_forbidden_access(self, mock_groq):
        mock_client = Mock()
        mock_client.chat.completions.create.side_effect = Exception("Unauthorized: Invalid API key")
        mock_groq.return_value = mock_client

        service = CausesService()
        prompt = "Test prompt"
        with self.assertRaises(Exception):
            service.api_call(prompt)

    def test_rca_row_1(self):
        question_id = uuid.uuid4()
        question = Question.objects.create(pk=question_id, question='Test question')
        cause1 = Causes.objects.create(problem=question, row=1, column=1, mode='PRIBADI', cause='Cause 1')
        cause2 = Causes.objects.create(problem=question, row=1, column=2, mode='PRIBADI', cause='Cause 2')

        with patch.object(CausesService, 'api_call', return_value=True):
            service = CausesService()
            service.validate(question_id)

        cause1.refresh_from_db()
        cause2.refresh_from_db()
        self.assertTrue(cause1.status)
        self.assertTrue(cause2.status)

    def test_rca_row_greater_than_1_with_prev_cause(self):
        question_id = uuid.uuid4()
        question = Question.objects.create(pk=question_id, question='Test question')

        Causes.objects.create(problem=question, row=1, column=1, mode='PRIBADI', cause='Cause 1', status=True)
        cause2 = Causes.objects.create(problem=question, row=2, column=1, mode='PRIBADI', cause='Cause 2')

        with patch.object(CausesService, 'api_call', return_value=True):
            service = CausesService()
            service.validate(question_id)

        cause2.refresh_from_db()
        self.assertTrue(cause2.status)

    def test_process_causes(self):
        question_id = uuid.uuid4()
        question = Question.objects.create(pk=question_id, question='Test question')

        cause1 = Causes.objects.create(problem=question, row=1, column=1, mode='PRIBADI', cause='Cause 1', status=True)

        with patch.object(CausesService, 'api_call'):
            service = CausesService()
            service.validate(question_id)

        self.assertTrue(cause1.status)