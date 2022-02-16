# Generated by Django 3.2.12 on 2022-02-18 13:13

from django.db import migrations, models
import django.db.models.deletion
import filer.fields.file
import mptt.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('filer', '0012_file_mime_type'),
        ('pdc', '0022_question'),
    ]

    operations = [
        migrations.CreateModel(
            name='QuestionnaireStep',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('parent_answer', models.CharField(blank=True, help_text='Dit label wordt getoond bij de keuzes van de vorige stap.', max_length=255, verbose_name='Antwoord op vorige vraag')),
                ('title', models.CharField(blank=True, help_text='Titel van deze stap, wordt overgenomen van de hoofdstap indien leeggelaten.', max_length=255, verbose_name='Titel')),
                ('description', models.CharField(blank=True, help_text='Deze tekst wordt ter ondersteuning onder de titel getoond, wordt overgenomen van de hoofdstap indien leeggelaten.', max_length=255, verbose_name='Beschrijving')),
                ('question', models.CharField(help_text='De stelling of vraag', max_length=255, verbose_name='Vraag')),
                ('slug', models.SlugField(max_length=255, verbose_name='URL vriendelijke naam')),
                ('help_text', models.CharField(default='Kies het antwoord dat het meest van toepassing is', help_text='Beschrijvende tekst bij de vraag.', max_length=510, verbose_name='Ondersteunende tekst')),
                ('content', models.TextField(blank=True, help_text='Deze inhoud wordt weergegeven in deze stap.', verbose_name='Uitgebreide informatie')),
                ('lft', models.PositiveIntegerField(editable=False)),
                ('rght', models.PositiveIntegerField(editable=False)),
                ('tree_id', models.PositiveIntegerField(db_index=True, editable=False)),
                ('level', models.PositiveIntegerField(editable=False)),
                ('parent', mptt.fields.TreeForeignKey(blank=True, help_text='Geeft aan op welke stap dit een vervolgstap is.', null=True, on_delete=django.db.models.deletion.CASCADE, to='questionnaire.questionnairestep', verbose_name='Vorige stap')),
                ('related_products', models.ManyToManyField(blank=True, help_text='Deze producten worden weergegeven in deze stap.', to='pdc.Product')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='QuestionnaireStepFile',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file', filer.fields.file.FilerFileField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='filer.file')),
                ('questionnaire_step', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='questionnaire.questionnairestep')),
            ],
            options={
                'verbose_name': 'Questionnaire step file',
                'verbose_name_plural': 'Questionnaire step files',
            },
        ),
    ]
