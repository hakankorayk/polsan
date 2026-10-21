"""Spec 0003: required birth date. Added nullable, checked, then made NOT NULL — no placeholder
default, which would silently break BR-2 (plan 0003, risk 7)."""

from django.db import migrations, models


def refuse_existing_rows(apps, schema_editor) -> None:  # noqa: ANN001
    employee = apps.get_model("employees", "Employee")
    if employee.objects.filter(birth_date__isnull=True).exists():
        raise RuntimeError(
            "Doğum tarihi olmayan çalışan kayıtları var. Önce doğum tarihlerini girin veya "
            "geliştirme veritabanını sıfırlayın (spec 0003, plan risk 7)."
        )


class Migration(migrations.Migration):
    dependencies = [("employees", "0001_initial")]

    operations = [
        migrations.AddField(
            model_name="employee",
            name="birth_date",
            field=models.DateField(null=True, verbose_name="doğum tarihi"),
        ),
        migrations.RunPython(refuse_existing_rows, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="employee",
            name="birth_date",
            field=models.DateField(verbose_name="doğum tarihi"),
        ),
    ]
