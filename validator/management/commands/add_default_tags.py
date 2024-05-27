from django.core.management.base import BaseCommand
from validator.models.question import Question
from validator.models.tag import Tag

class Command(BaseCommand):
    help = 'Add default tag "analisis" to existing questions'

    def handle(self, *args, **kwargs):
        default_tag, _ = Tag.objects.get_or_create(name='analisis')

        questions = Question.objects.all()
        for question in questions:
            question.tags.add(default_tag)

        self.stdout.write(self.style.SUCCESS('Successfully added default tag "analisis" to existing questions.'))
