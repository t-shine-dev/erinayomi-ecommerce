import django, os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "erinayomi.settings")
django.setup()
from catalog.models import Category, Product
from store_settings.models import StoreSettings

s = StoreSettings.load()
s.business_email = "temitopesunday005@gmail.com"
s.phone_number = "+234 810 860 7409"
s.whatsapp_number = "+2348108607409"
s.address = "12 Adeola Odeku Street, Victoria Island, Lagos"
s.business_hours = "Mon–Sat, 9am–7pm"
s.instagram_link = "https://instagram.com/erinayomi"
s.save()

rings, _ = Category.objects.get_or_create(name="Rings")
watches, _ = Category.objects.get_or_create(name="Watches")
tailoring, _ = Category.objects.get_or_create(name="Tailoring")
accessories, _ = Category.objects.get_or_create(name="Accessories")

products = [
    ("Adaeze Gold Band Ring", rings, "ring", 85000, "RNG-001", 12, True),
    ("Emerald Halo Ring", rings, "ring", 145000, "RNG-002", 5, True),
    ("Classic Steel Chronograph", watches, "watch", 210000, "WCH-001", 8, True),
    ("Rose Gold Dress Watch", watches, "watch", 265000, "WCH-002", 3, True),
    ("Bespoke Agbada, Made to Measure", tailoring, "tailoring", 180000, "TLR-001", 20, False),
    ("Tailored Kaftan", tailoring, "tailoring", 95000, "TLR-002", 15, False),
    ("Beaded Statement Necklace", accessories, "jewelry", 42000, "ACC-001", 25, True),
    ("Leather Card Wallet", accessories, "accessory", 18000, "ACC-002", 40, False),
]
for name, cat, ptype, price, sku, stock, featured in products:
    Product.objects.get_or_create(
        sku=sku,
        defaults=dict(
            name=name, category=cat, product_type=ptype, price=price,
            stock=stock, is_featured=featured, is_active=True,
            description="A refined piece from the ERINAYOMI collection, crafted for everyday elegance.",
        ),
    )
print("Seed complete:", Product.objects.count(), "products")
