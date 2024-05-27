from django.db import models
import uuid
from validator.models import Question

class Causes(models.Model):
    class Meta:
        app_label = 'validator'
        
    class ModeChoices(models.TextChoices):
        PRIBADI = "PRIBADI", "pribadi"
        PENGAWASAN = "PENGAWASAN", "pengawasan"
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    problem = models.ForeignKey(Question, on_delete=models.SET_NULL, null=True)
    row = models.IntegerField()
    column = models.IntegerField()
    mode = models.CharField(max_length = 20, choices=ModeChoices.choices, default=ModeChoices.PRIBADI)
    cause = models.CharField(max_length = 120)
    status = models.BooleanField(default=False)
    root_status = models.BooleanField(default=False)
    feedback = models.CharField(max_length = 50, default='')