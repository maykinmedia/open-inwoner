# Generated by Django 3.2.13 on 2022-06-08 14:34

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="CSPSetting",
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
                    "directive",
                    models.CharField(
                        choices=[
                            ("default-src", "default-src"),
                            ("script-src", "script-src"),
                            ("script-src-attr", "script-src-attr"),
                            ("script-src-elem", "script-src-elem"),
                            ("img-src", "img-src"),
                            ("object-src", "object-src"),
                            ("prefetch-src", "prefetch-src"),
                            ("media-src", "media-src"),
                            ("frame-src", "frame-src"),
                            ("font-src", "font-src"),
                            ("connect-src", "connect-src"),
                            ("style-src", "style-src"),
                            ("style-src-attr", "style-src-attr"),
                            ("style-src-elem", "style-src-elem"),
                            ("base-uri", "base-uri"),
                            ("child-src", "child-src"),
                            ("frame-ancestors", "frame-ancestors"),
                            ("navigate-to", "navigate-to"),
                            ("form-action", "form-action"),
                            ("sandbox", "sandbox"),
                            ("report-uri", "report-uri"),
                            ("report-to", "report-to"),
                            ("manifest-src", "manifest-src"),
                            ("worker-src", "worker-src"),
                            ("plugin-types", "plugin-types"),
                            ("require-sri-for", "require-sri-for"),
                        ],
                        help_text="CSP header directive",
                        max_length=64,
                        verbose_name="directive",
                    ),
                ),
                (
                    "value",
                    models.CharField(
                        help_text="CSP header value",
                        max_length=128,
                        verbose_name="value",
                    ),
                ),
            ],
            options={
                "ordering": ("directive", "value"),
            },
        ),
    ]
