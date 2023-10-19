# Generated by Django 3.2.20 on 2023-09-19 11:53

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Video",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "link_id",
                    models.CharField(
                        help_text="https://vimeo.com/[Video ID] | https://www.youtube.com/watch?v=[Video ID]",
                        max_length=100,
                        verbose_name="video ID",
                    ),
                ),
                (
                    "player_type",
                    models.CharField(
                        choices=[("vimeo", "Vimeo"), ("youtube", "Youtube")],
                        default="vimeo",
                        max_length=200,
                        verbose_name="Player type",
                    ),
                ),
                (
                    "title",
                    models.CharField(
                        blank=True, default="", max_length=200, verbose_name="title"
                    ),
                ),
                (
                    "language",
                    models.CharField(
                        choices=[("nl", "Dutch")],
                        default="nl",
                        max_length=20,
                        verbose_name="language",
                    ),
                ),
            ],
            options={
                "verbose_name": "Video",
                "ordering": ("title",),
            },
        ),
    ]