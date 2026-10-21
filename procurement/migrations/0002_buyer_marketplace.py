from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('procurement', '0001_initial'),
    ]

    operations = [
        # Extend User.role max_length for BUYER
        migrations.AlterField(
            model_name='user',
            name='role',
            field=models.CharField(
                choices=[
                    ('FARMER',  'Farmer'),
                    ('OFFICER', 'Procurement Officer'),
                    ('ADMIN',   'Administrator'),
                    ('BUYER',   'Private Buyer'),
                ],
                max_length=10,
            ),
        ),

        # Buyer
        migrations.CreateModel(
            name='Buyer',
            fields=[
                ('id',           models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('company_name', models.CharField(max_length=200)),
                ('buyer_type',   models.CharField(choices=[('RICE_MILL','Rice Mill'),('WHOLESALER','Wholesaler'),('EXPORTER','Exporter'),('PROCESSOR','Food Processor')], max_length=20)),
                ('license_no',   models.CharField(blank=True, max_length=100)),
                ('gst_number',   models.CharField(blank=True, max_length=20)),
                ('address',      models.TextField()),
                ('district',     models.CharField(max_length=100)),
                ('state',        models.CharField(default='Andhra Pradesh', max_length=100)),
                ('contact_name', models.CharField(max_length=100)),
                ('status',       models.CharField(choices=[('PENDING','Pending Approval'),('APPROVED','Approved'),('BLOCKED','Blocked')], default='PENDING', max_length=20)),
                ('rating',       models.DecimalField(decimal_places=1, default=0.0, max_digits=3)),
                ('total_deals',  models.IntegerField(default=0)),
                ('created_at',   models.DateTimeField(auto_now_add=True)),
                ('updated_at',   models.DateTimeField(auto_now=True)),
                ('user',         models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='buyer_profile', to=settings.AUTH_USER_MODEL)),
            ],
            options={'db_table': 'marketplace_buyer'},
        ),

        # BuyerOffer
        migrations.CreateModel(
            name='BuyerOffer',
            fields=[
                ('id',                 models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('price_per_quintal',  models.DecimalField(decimal_places=2, max_digits=10)),
                ('min_quantity_qtl',   models.DecimalField(decimal_places=2, default=1, max_digits=8)),
                ('max_quantity_qtl',   models.DecimalField(decimal_places=2, max_digits=8)),
                ('valid_from',         models.DateField()),
                ('valid_until',        models.DateField()),
                ('pickup_location',    models.CharField(max_length=200)),
                ('description',        models.TextField(blank=True)),
                ('status',             models.CharField(choices=[('ACTIVE','Active'),('CLOSED','Closed'),('EXPIRED','Expired'),('PAUSED','Paused')], default='ACTIVE', max_length=20)),
                ('advance_percent',    models.IntegerField(default=0)),
                ('payment_days',       models.IntegerField(default=7)),
                ('created_at',         models.DateTimeField(auto_now_add=True)),
                ('updated_at',         models.DateTimeField(auto_now=True)),
                ('buyer',  models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='offers',       to='procurement.buyer')),
                ('crop',   models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='buyer_offers', to='procurement.crop')),
            ],
            options={'db_table': 'marketplace_buyer_offer', 'ordering': ['-price_per_quintal']},
        ),

        # FarmerDeal
        migrations.CreateModel(
            name='FarmerDeal',
            fields=[
                ('id',               models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('quantity_qtl',     models.DecimalField(decimal_places=2, max_digits=8)),
                ('agreed_price',     models.DecimalField(decimal_places=2, max_digits=10)),
                ('total_amount',     models.DecimalField(decimal_places=2, max_digits=12)),
                ('status',           models.CharField(choices=[('PENDING','Pending Confirmation'),('CONFIRMED','Confirmed by Buyer'),('DELIVERED','Crop Delivered'),('PAID','Payment Done'),('CANCELLED','Cancelled'),('DISPUTED','Disputed')], default='PENDING', max_length=20)),
                ('delivery_date',    models.DateField(blank=True, null=True)),
                ('delivery_address', models.CharField(blank=True, max_length=300)),
                ('farmer_notes',     models.TextField(blank=True)),
                ('buyer_notes',      models.TextField(blank=True)),
                ('dispute_reason',   models.TextField(blank=True)),
                ('ai_recommendation',models.TextField(blank=True)),
                ('created_at',       models.DateTimeField(auto_now_add=True)),
                ('updated_at',       models.DateTimeField(auto_now=True)),
                ('farmer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='deals',  to='procurement.farmer')),
                ('offer',  models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='deals',  to='procurement.buyeroffer')),
            ],
            options={'db_table': 'marketplace_farmer_deal', 'ordering': ['-created_at']},
        ),
    ]
