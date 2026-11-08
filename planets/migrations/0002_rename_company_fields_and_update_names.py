from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("planets", "0001_initial"),
    ]

    operations = [
        migrations.RenameField(
            model_name="company",
            old_name="CEO",
            new_name="ceo",
        ),
        migrations.RenameField(
            model_name="company",
            old_name="revenue_2025",
            new_name="annual_revenue",
        ),
        migrations.AlterField(
            model_name="company",
            name="annual_revenue",
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                help_text="В миллионах долларов США",
                max_digits=15,
                null=True,
                verbose_name="Годовая выручка (млн USD)",
            ),
        ),
        migrations.AlterField(
            model_name="company",
            name="image",
            field=models.ImageField(
                blank=True,
                null=True,
                upload_to="companies/",
                verbose_name="Изображение компании",
            ),
        ),
        migrations.AlterField(
            model_name="planet",
            name="name",
            field=models.CharField(max_length=20, verbose_name="Название планеты"),
        ),
        migrations.AlterField(
            model_name="satellite",
            name="name",
            field=models.CharField(max_length=20, verbose_name="Название спутника"),
        ),
    ]
