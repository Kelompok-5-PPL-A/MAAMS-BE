from django.test import TestCase
from unittest.mock import patch, Mock
from django.conf import settings
from validator.services.causes import CausesService
from validator.models.causes import Causes
from validator.models.question import Question
from validator.enums import ValidationType
from validator.constants import FeedbackMsg
import uuid
from requests.exceptions import RequestException
from validator.exceptions import AIServiceErrorException

class CausesServiceTest(TestCase):
    @patch('validator.services.causes.Groq')
    def test_api_call_positive(self, mock_groq):
        mock_client = Mock()
        mock_chat_completion = Mock()
        mock_chat_completion.choices = [Mock(message=Mock(content='true'))]
        mock_client.chat.completions.create.return_value = mock_chat_completion
        mock_groq.return_value = mock_client

        service = CausesService()
        system_message = "You are an AI model. You are asked to determine whether the given cause is the cause of the given problem."
        user_prompt = "Is 'Example cause' the cause of 'Example problem'? Answer only with True/False"
        response = service.api_call(system_message, user_prompt, ValidationType.NORMAL)

        self.assertEqual(response, 1)
        mock_client.chat.completions.create.assert_called_once_with(
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

    @patch('validator.services.causes.Groq')
    def test_api_call_returns_false(self, mock_groq):
        mock_client = Mock()
        mock_chat_completion = Mock()
        mock_chat_completion.choices = [Mock(message=Mock(content='false'))]
        mock_client.chat.completions.create.return_value = mock_chat_completion
        mock_groq.return_value = mock_client

        service = CausesService()
        system_message = "You are an AI model. You are asked to determine whether the given cause is the cause of the given problem."
        user_prompt = "Is 'Example cause' the cause of 'Example problem'? Answer only with True/False"
        response = service.api_call(system_message, user_prompt, ValidationType.NORMAL)

        self.assertEqual(response, 0)
        mock_client.chat.completions.create.assert_called_once_with(
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

    @patch('validator.services.causes.Groq')
    def test_api_call_request_exception(self, mock_groq):
        mock_client = Mock()
        mock_client.chat.completions.create.side_effect = RequestException("Network error")
        mock_groq.return_value = mock_client

        service = CausesService()
        system_message = "You are an AI model. You are asked to determine whether the given cause is the cause of the given problem."
        user_prompt = "Is 'Example cause' the cause of 'Example problem'? Answer only with True/False"

        with self.assertRaises(AIServiceErrorException) as context:
            service.api_call(system_message, user_prompt, ValidationType.NORMAL)

        mock_client.chat.completions.create.assert_called_once_with(
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

        self.assertTrue("Failed to call the AI service." in str(context.exception))

    @patch('validator.services.causes.Groq')
    def test_api_call_negative(self, mock_groq):
        mock_client = Mock()
        mock_client.chat.completions.create.side_effect = Exception("API call failed")
        mock_groq.return_value = mock_client

        service = CausesService()
        system_message = "You are an AI model. You are asked to determine whether the given cause is the cause of the given problem."
        user_prompt = "test prompt"
        with self.assertRaises(Exception):
            service.api_call(system_message, user_prompt, ValidationType.NORMAL)

    @patch('validator.services.causes.Groq')
    def test_api_call_forbidden_access(self, mock_groq):
        mock_client = Mock()
        mock_client.chat.completions.create.side_effect = Exception("Unauthorized: Invalid API key")
        mock_groq.return_value = mock_client

        service = CausesService()
        system_message = "You are an AI model. You are asked to determine whether the given cause is the cause of the given problem."
        user_prompt = "Test prompt"
        with self.assertRaises(Exception):
            service.api_call(system_message, user_prompt, ValidationType.NORMAL)

    def test_rca_row_1(self):
        question_id = uuid.uuid4()
        question = Question.objects.create(pk=question_id, question='Test question')
        cause1 = Causes.objects.create(problem=question, row=1, column=1, mode='PRIBADI', cause='Cause 1')
        cause2 = Causes.objects.create(problem=question, row=1, column=2, mode='PRIBADI', cause='Cause 2')

        with patch.object(CausesService, 'api_call', return_value=1):
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

        with patch.object(CausesService, 'api_call', return_value=1):
            service = CausesService()
            service.validate(question_id)

        cause2.refresh_from_db()
        self.assertTrue(cause2.status)

    @patch('validator.services.causes.Groq')
    def test_check_root_cause(self, mock_groq):
        mock_client = Mock()
        mock_chat_completion = Mock()
        mock_chat_completion.choices = [Mock(message=Mock(content='true'))]
        mock_client.chat.completions.create.return_value = mock_chat_completion
        mock_groq.return_value = mock_client

        service = CausesService()
        cause = Causes(problem_id=uuid.uuid4(), cause="Root Cause", row=1, column=1)
        problem = Question(question="Test problem")

        service.check_root_cause(cause, problem)
        self.assertTrue(cause.root_status)

    @patch('validator.services.causes.Groq')
    def test_retrieve_feedback_not_cause_1_row(self, mock_groq):
        mock_client = Mock()
        mock_chat_completion = Mock()
        mock_chat_completion.choices = [Mock(message=Mock(content='1'))]
        mock_client.chat.completions.create.return_value = mock_chat_completion
        mock_groq.return_value = mock_client

        service = CausesService()
        cause = Causes(problem_id=uuid.uuid4(), cause="False Cause", row=1, column=1)
        problem = Question(question="Test problem")

        service.retrieve_feedback(cause, problem, None)
        self.assertEqual(cause.feedback, FeedbackMsg.FALSE_ROW_1_NOT_CAUSE.format(column='B'))

    @patch('validator.services.causes.Groq')
    def test_retrieve_feedback_positive_neutral_1_row(self, mock_groq):
        mock_client = Mock()
        mock_chat_completion = Mock()
        mock_chat_completion.choices = [Mock(message=Mock(content='2'))]
        mock_client.chat.completions.create.return_value = mock_chat_completion
        mock_groq.return_value = mock_client

        service = CausesService()
        cause = Causes(problem_id=uuid.uuid4(), cause="Positive/Neutral Cause", row=1, column=1)
        problem = Question(question="Test problem")

        service.retrieve_feedback(cause, problem, None)
        self.assertEqual(cause.feedback, FeedbackMsg.FALSE_ROW_N_POSITIVE_NEUTRAL.format(column='B', row=1))

    @patch('validator.services.causes.Groq')
    def test_retrieve_feedback_not_cause_n_row(self, mock_groq):
        mock_client = Mock()
        mock_chat_completion = Mock()
        mock_chat_completion.choices = [Mock(message=Mock(content='1'))]
        mock_client.chat.completions.create.return_value = mock_chat_completion
        mock_groq.return_value = mock_client

        service = CausesService()
        prev_cause = Causes(problem_id=uuid.uuid4(), cause="Base Cause", row=1, column=1)
        cause = Causes(problem_id=uuid.uuid4(), cause="False Cause", row=2, column=1)
        problem = Question(question="Test problem")

        service.retrieve_feedback(cause, problem, prev_cause)
        self.assertEqual(cause.feedback, FeedbackMsg.FALSE_ROW_N_NOT_CAUSE.format(column='B', row=2, prev_row=1))

    @patch('validator.services.causes.Groq')
    def test_retrieve_feedback_positive_neutral_n_row(self, mock_groq):
        mock_client = Mock()
        mock_chat_completion = Mock()
        mock_chat_completion.choices = [Mock(message=Mock(content='2'))]
        mock_client.chat.completions.create.return_value = mock_chat_completion
        mock_groq.return_value = mock_client

        service = CausesService()
        prev_cause = Causes(problem_id=uuid.uuid4(), cause="Base Cause", row=1, column=1)
        cause = Causes(problem_id=uuid.uuid4(), cause="Positive/Neutral Cause", row=2, column=1)
        problem = Question(question="Test problem")

        service.retrieve_feedback(cause, problem, prev_cause)
        self.assertEqual(cause.feedback, FeedbackMsg.FALSE_ROW_N_POSITIVE_NEUTRAL.format(column='B', row=2))

    @patch('validator.services.causes.Groq')
    def test_retrieve_feedback_similar_previous_n_row(self, mock_groq):
        mock_client = Mock()
        mock_chat_completion = Mock()
        mock_chat_completion.choices = [Mock(message=Mock(content='3'))]
        mock_client.chat.completions.create.return_value = mock_chat_completion
        mock_groq.return_value = mock_client

        service = CausesService()
        cause = Causes(problem_id=uuid.uuid4(), cause="Similar Cause", row=2, column=1)
        prev_cause = Causes(problem_id=uuid.uuid4(), cause="Previous Cause", row=1, column=1)
        problem = Question(question="Test problem")

        service.retrieve_feedback(cause, problem, prev_cause)
        self.assertEqual(cause.feedback, FeedbackMsg.FALSE_ROW_N_SIMILAR_PREVIOUS.format(column='B', row=2))

    def test_process_causes(self):
        question_id = uuid.uuid4()
        question = Question.objects.create(pk=question_id, question='Test question')

        cause1 = Causes.objects.create(problem=question, row=1, column=1, mode='PRIBADI', cause='Cause 1', status=True)

        with patch.object(CausesService, 'api_call'):
            service = CausesService()
            service.validate(question_id)

        self.assertTrue(cause1.status)
