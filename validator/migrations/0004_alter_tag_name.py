# Generated by Django 4.2 on 2024-04-28 09:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('validator', '0003_tag_question_title_question_tags'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tag',
            name='name',
            field=models.CharField(max_length=10, unique=True),
        ),
    ]
