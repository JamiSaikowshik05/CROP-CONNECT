"""
Management command to seed initial data for CropConnect
"""
from datetime import date, timedelta
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from procurement.models import Crop, Slot, Announcement, Buyer, BuyerOffer

User = get_user_model()


class Command(BaseCommand):
    help = 'Seed crops, slots, announcements, sample users, and marketplace buyers'

    def handle(self, *args, **options):
        # Crops
        paddy, _ = Crop.objects.get_or_create(name='Paddy', defaults={'msp_per_quintal': 2441, 'season': 'Kharif 2026-27'})
        groundnut, _ = Crop.objects.get_or_create(name='Groundnut', defaults={'msp_per_quintal': 7517, 'season': 'Kharif 2026-27'})
        self.stdout.write('Created crops: Paddy, Groundnut')

        # Slots for next 14 days
        base = date.today()
        for i in range(14):
            d = base + timedelta(days=i)
            Slot.objects.get_or_create(date=d, crop=paddy, defaults={'total_capacity_quintals': 500, 'booked_capacity': 0})
            Slot.objects.get_or_create(date=d, crop=groundnut, defaults={'total_capacity_quintals': 200, 'booked_capacity': 0})
        self.stdout.write('Created slots for 14 days')

        # Announcements
        Announcement.objects.get_or_create(
            title='MSP for Kharif 2026-27 Announced',
            defaults={
                'content': 'Minimum Support Price for Paddy (Common) is Rs 2,441 per quintal and for Groundnut (in shell) is Rs 7,517 per quintal for the Kharif marketing season 2026-27.',
                'is_active': True
            }
        )
        Announcement.objects.get_or_create(
            title='NEW: Private Buyer Marketplace Launched',
            defaults={
                'content': 'Farmers can now compare Government MSP offers with private rice mills, wholesalers, and exporters. Visit the Marketplace tab after login to see all offers.',
                'is_active': True
            }
        )
        self.stdout.write('Created announcements')

        # Create admin, officer, farmer sample users if not exist
        if not User.objects.filter(username='admin').exists():
            u = User.objects.create_superuser('admin', 'admin@cropconnect.gov.in', 'admin123')
            u.role = User.Role.ADMIN
            u.save()
            self.stdout.write('Created admin user: admin / admin123')

        if not User.objects.filter(username='officer1').exists():
            User.objects.create_user('officer1', 'officer@cropconnect.gov.in', 'officer123', role=User.Role.OFFICER, first_name='Procurement', last_name='Officer')
            self.stdout.write('Created officer: officer1 / officer123')

        # ── Sample Buyers ──
        buyer_data = [
            {
                'username': 'sriram_ricemill',
                'company': 'Sri Ram Rice Mill',
                'type': Buyer.BuyerType.RICE_MILL,
                'district': 'Guntur',
                'contact': 'Ramesh Kumar',
                'paddy_price': 2350,   # above MSP
                'gnut_price': None,
            },
            {
                'username': 'ap_wholesaler',
                'company': 'AP Agro Wholesale Pvt Ltd',
                'type': Buyer.BuyerType.WHOLESALER,
                'district': 'Krishna',
                'contact': 'Suresh Reddy',
                'paddy_price': 2250,
                'gnut_price': 6100,
            },
            {
                'username': 'export_india',
                'company': 'India Export Foods Ltd',
                'type': Buyer.BuyerType.EXPORTER,
                'district': 'Visakhapatnam',
                'contact': 'Priya Singh',
                'paddy_price': 2400,   # premium above MSP
                'gnut_price': 6500,
            },
        ]

        for bd in buyer_data:
            if not User.objects.filter(username=bd['username']).exists():
                buser = User.objects.create_user(
                    bd['username'], f"{bd['username']}@market.com", 'buyer123',
                    role=User.Role.BUYER,
                    first_name=bd['contact'].split()[0],
                )
                buyer = Buyer.objects.create(
                    user=buser,
                    company_name=bd['company'],
                    buyer_type=bd['type'],
                    district=bd['district'],
                    contact_name=bd['contact'],
                    address=f"Main Road, {bd['district']}, Andhra Pradesh",
                    status=Buyer.Status.APPROVED,
                    rating=4.2,
                    total_deals=12,
                )
                # Create offers for each buyer
                today = date.today()
                if bd['paddy_price']:
                    BuyerOffer.objects.get_or_create(
                        buyer=buyer, crop=paddy,
                        defaults={
                            'price_per_quintal': bd['paddy_price'],
                            'min_quantity_qtl': 5,
                            'max_quantity_qtl': 500,
                            'valid_from': today,
                            'valid_until': today + timedelta(days=30),
                            'pickup_location': f"Near Highway, {bd['district']}",
                            'description': f"Premium quality paddy procurement by {bd['company']}. Quick payment guaranteed.",
                            'advance_percent': 20,
                            'payment_days': 5,
                            'status': BuyerOffer.Status.ACTIVE,
                        }
                    )
                if bd['gnut_price']:
                    BuyerOffer.objects.get_or_create(
                        buyer=buyer, crop=groundnut,
                        defaults={
                            'price_per_quintal': bd['gnut_price'],
                            'min_quantity_qtl': 5,
                            'max_quantity_qtl': 200,
                            'valid_from': today,
                            'valid_until': today + timedelta(days=30),
                            'pickup_location': f"Warehouse, {bd['district']}",
                            'description': f"Groundnut procurement by {bd['company']}.",
                            'advance_percent': 10,
                            'payment_days': 7,
                            'status': BuyerOffer.Status.ACTIVE,
                        }
                    )
                self.stdout.write(f'Created buyer: {bd["username"]} / buyer123')

        self.stdout.write(self.style.SUCCESS('Seed completed. Marketplace buyers and offers created.'))
