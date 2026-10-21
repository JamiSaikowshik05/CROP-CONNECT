from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('procurement', '0002_buyer_marketplace'),
    ]

    operations = [
        migrations.AddField(model_name='procurement', name='moisture_percent',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True)),
        migrations.AddField(model_name='procurement', name='foreign_matter_percent',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True)),
        migrations.AddField(model_name='procurement', name='quality_grade',
            field=models.CharField(blank=True, max_length=10)),
        migrations.AddField(model_name='procurement', name='quality_passed',
            field=models.BooleanField(default=True)),
        migrations.AddField(model_name='procurement', name='rejection_reason',
            field=models.TextField(blank=True)),
        migrations.AddField(model_name='procurement', name='damaged_grains_percent',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True)),
        migrations.AddField(model_name='procurement', name='immature_grains_percent',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True)),
        migrations.AddField(model_name='procurement', name='chalky_grains_percent',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True)),
        migrations.AddField(model_name='procurement', name='shelling_percent',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True)),
        migrations.AddField(model_name='procurement', name='oil_content_percent',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True)),
        migrations.AddField(model_name='procurement', name='aflatoxin_present',
            field=models.BooleanField(default=False)),
    ]
