from django.test import TestCase
from unittest.mock import patch
from django.conf import settings
from validator.services.causes import CausesService
import openai
from validator.models.causes import Causes
from validator.models.question import Question
import uuid
import json

class CausesServiceTest(TestCase):
    @patch('openai.Completion.create')
    def test_api_call_positive(self, mock_completion_create):
        mock_completion_create.return_value.choices[0].text = "test response"

        service = CausesService()
        prompt = "test prompt"
        response = service.api_call(prompt)

        self.assertEqual(response, "test response")
        mock_completion_create.assert_called_once_with(
            model="gpt-3.5-turbo",
            prompt=prompt,
            max_tokens=1,
            n=3,
            temperature=0
        )

    @patch('openai.Completion.create')
    def test_api_call_negative(self, mock_completion_create):
        mock_completion_create.side_effect = Exception("API call failed")

        service = CausesService()
        prompt = "" 
        with self.assertRaises(Exception):
            service.api_call(prompt)

    @patch('openai.Completion.create')
    def test_api_call_special_chars(self, mock_completion_create):
        mock_completion_create.return_value.choices[0].text = "!@#$%^&*()_+"

        service = CausesService()
        prompt = "!@#$%^&*()_+"
        response = service.api_call(prompt)

        self.assertEqual(response, "!@#$%^&*()_+")

    @patch('openai.Completion.create')
    def test_api_call_forbidden_access(self, mock_completion_create):
        mock_completion_create.side_effect = openai.OpenAIError("Unauthorized: Invalid API key")

        service = CausesService()
        prompt = "Test prompt"
        with self.assertRaises(openai.OpenAIError):
            service.api_call(prompt)
    
    def test_rca_row_1(self):
        question_id = uuid.uuid4()
        question = Question.objects.create(pk=question_id, question='Test question')
        cause1 = Causes.objects.create(problem=question, row=1, column=1, mode='PRIBADI', cause='Cause 1', status=False)
        cause2 = Causes.objects.create(problem=question, row=1, column=2, mode='PRIBADI', cause='Cause 2', status=False)
        
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

        Causes.objects.create(problem=question, row=1, column=1, mode='PRIBADI', cause='Cause 1', status=False)
        cause2 = Causes.objects.create(problem=question, row=2, column=1, mode='PRIBADI', cause='Cause 1')

        with patch.object(CausesService, 'api_call', return_value=True):
            service = CausesService()
            service.validate(question_id)

        cause2.refresh_from_db()

        self.assertTrue(cause2.status)

    def test_validate_all_causes_true_exception(self):
        question_id = uuid.uuid4()
        question = Question.objects.create(pk=question_id, question='Test question')

        Causes.objects.create(problem=question, row=1, column=1, mode='PRIBADI', cause='Cause 1', status=True)
        Causes.objects.create(problem=question, row=1, column=2, mode='PRIBADI', cause='Cause 2', status=True)

        with patch.object(CausesService, 'api_call', side_effect=Exception("No cause to validate")):
            with self.assertRaises(Exception) as context:
                service = CausesService()
                service.validate(question_id)
    
        self.assertEqual(str(context.exception), "No cause to validate")