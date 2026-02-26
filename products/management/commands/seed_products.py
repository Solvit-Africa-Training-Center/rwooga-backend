import random
import requests
import io
from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from django.utils import timezone
from products.models import ServiceCategory, Product, ProductMedia, Feedback, Discount, ProductDiscount


# ─── Category definitions ─────────────────────────────────────────────────────

CATEGORIES = [
    {
        "name": "3D Printing",
        "requires_dimensions": True,
        "requires_material": True,
        "is_active": True,
    },
    {
        "name": "3D Visualization",
        "requires_dimensions": False,
        "requires_material": False,
        "is_active": True,
    },
    {
        "name": "Animation & Video",
        "requires_dimensions": False,
        "requires_material": False,
        "is_active": True,
    },
    {
        "name": "Custom 3D Design",
        "requires_dimensions": True,
        "requires_material": True,
        "is_active": True,
    },
]

# Each product has a unique Picsum seed so images are deterministic and varied.
PRODUCTS = [
    # ── 3D Printing ──────────────────────────────────────────────────────────
    {
        "category": "3D Printing",
        "name": "Geometric Planter",
        "short_description": "Stylish hexagonal planter printed in eco-friendly PLA.",
        "detailed_description": (
            "This modern geometric planter is perfect for succulents and small indoor plants. "
            "Printed in high-quality PLA with a honeycomb lattice structure that allows drainage. "
            "Available in multiple colour options and three sizes."
        ),
        "unit_price": "15000.00",
        "length": "12.00", "width": "12.00", "height": "15.00",
        "available_sizes": "Small,Medium,Large",
        "available_colors": "Cyan,White,Black,Terracotta",
        "available_materials": "PLA,PETG",
        "published": True,
        "image_seeds": ["planter", "plant", "succulent"],
    },
    {
        "category": "3D Printing",
        "name": "Minimalist Phone Stand",
        "short_description": "Sleek desktop phone stand with cable management groove.",
        "detailed_description": (
            "A clean, modern phone stand that holds your device at the perfect viewing angle. "
            "Features a built-in groove to route charging cables cleanly. "
            "Compatible with all phone sizes."
        ),
        "unit_price": "8000.00",
        "length": "10.00", "width": "8.00", "height": "9.00",
        "available_sizes": "Standard",
        "available_colors": "Silver,Gold,Black,White",
        "available_materials": "PLA",
        "published": True,
        "image_seeds": ["desk", "minimal", "tech"],
    },
    {
        "category": "3D Printing",
        "name": "Articulated Dragon",
        "short_description": "Fully articulated dragon figurine — flexible and poseable.",
        "detailed_description": (
            "A stunning print-in-place dragon that is fully articulated right off the printer. "
            "Each segment is printed individually and linked, so no assembly is needed. "
            "Makes an exceptional collector's piece or gift."
        ),
        "unit_price": "25000.00",
        "length": "30.00", "width": "8.00", "height": "6.00",
        "available_sizes": "Medium,Large",
        "available_colors": "Rainbow Silk,Galaxy Blue,Copper",
        "available_materials": "Silk PLA,PETG",
        "published": True,
        "image_seeds": ["dragon", "fantasy", "figurine"],
    },
    {
        "category": "3D Printing",
        "name": "Custom Name Keychain",
        "short_description": "Personalised keychain printed with any name or logo.",
        "detailed_description": (
            "A great personalised gift — we print your name, initials, or a small logo on a "
            "durable, lightweight keychain. Available in dozens of colour combinations."
        ),
        "unit_price": "3500.00",
        "length": "6.00", "width": "2.50", "height": "0.50",
        "available_sizes": "Standard",
        "available_colors": "Any",
        "available_materials": "PLA,PETG,Resin",
        "published": True,
        "image_seeds": ["gift", "keychain", "custom"],
    },
    {
        "category": "3D Printing",
        "name": "Wall-Mount Cable Organiser",
        "short_description": "Clip-on cable organiser for a clean, tidy workspace.",
        "detailed_description": (
            "Keep your desk free from cable clutter with these adhesive-backed cable clips. "
            "Sold in packs of 5. Supports cables from 3 mm to 8 mm in diameter."
        ),
        "unit_price": "5000.00",
        "length": "4.00", "width": "3.00", "height": "2.00",
        "available_sizes": "Pack of 5,Pack of 10",
        "available_colors": "White,Black,Grey",
        "available_materials": "PLA",
        "published": True,
        "image_seeds": ["cable", "workspace", "organizer"],
    },

    # ── 3D Visualization ─────────────────────────────────────────────────────
    {
        "category": "3D Visualization",
        "name": "Architectural Interior Render",
        "short_description": "Photorealistic interior rendering for residential or commercial spaces.",
        "detailed_description": (
            "Transform your architectural plans into stunning, photorealistic 3D renders. "
            "Each render is delivered in 4K resolution with realistic lighting, materials, and shadows. "
            "Ideal for presentations, marketing, and client approvals."
        ),
        "unit_price": "120000.00",
        "available_sizes": "Single Room,Full Floor,Full Building",
        "published": True,
        "image_seeds": ["interior", "architecture", "room"],
    },
    {
        "category": "3D Visualization",
        "name": "Product Showcase Render",
        "short_description": "High-end 3D product renders ready for e-commerce and advertising.",
        "detailed_description": (
            "Get studio-quality product images without a physical prototype. "
            "We create detailed 3D models of your product and render them from multiple angles "
            "with professional lighting setups suitable for online stores and print campaigns."
        ),
        "unit_price": "80000.00",
        "available_sizes": "3 Angles,6 Angles,360 Spin",
        "published": True,
        "image_seeds": ["product", "render", "studio"],
    },

    # ── Animation & Video ─────────────────────────────────────────────────────
    {
        "category": "Animation & Video",
        "name": "Product Commercial Animation",
        "short_description": "30-second animated product commercial for social media.",
        "detailed_description": (
            "A fully animated 30-second commercial showcasing your product in action. "
            "Includes motion graphics, sound design, and colour grading. "
            "Delivered in 1080p/4K, optimised for Instagram, TikTok, and YouTube."
        ),
        "unit_price": "350000.00",
        "available_sizes": "15 sec,30 sec,60 sec",
        "published": True,
        "image_seeds": ["animation", "commercial", "video"],
    },
    {
        "category": "Animation & Video",
        "name": "Explainer Animation",
        "short_description": "Engaging 2D/3D explainer video for your business or product.",
        "detailed_description": (
            "Communicate complex ideas simply with a professionally animated explainer. "
            "We handle script, voiceover coordination, animation, and delivery. "
            "Great for startups, pitch decks, and social media marketing."
        ),
        "unit_price": "250000.00",
        "available_sizes": "60 sec,90 sec,2 min",
        "published": True,
        "image_seeds": ["explainer", "business", "startup"],
    },

    # ── Custom 3D Design ──────────────────────────────────────────────────────
    {
        "category": "Custom 3D Design",
        "name": "Custom Figurine",
        "short_description": "Your portrait or character turned into a detailed 3D figurine.",
        "detailed_description": (
            "We sculpt a highly detailed 3D model based on your photos or sketch, then print it "
            "with a resin printer for ultra-fine detail. Makes the perfect personalised gift."
        ),
        "unit_price": "55000.00",
        "length": "8.00", "width": "8.00", "height": "20.00",
        "available_sizes": "10 cm,15 cm,20 cm",
        "available_colors": "Natural Resin,Painted",
        "available_materials": "Resin",
        "published": True,
        "image_seeds": ["figurine", "portrait", "sculpture"],
    },
    {
        "category": "Custom 3D Design",
        "name": "Mechanical Part Prototyping",
        "short_description": "Custom engineering parts modelled and printed to your specifications.",
        "detailed_description": (
            "Provide a sketch or dimensions and we'll produce a precision-accurate CAD model "
            "and prototype. Suitable for replacement parts, jigs, brackets, and enclosures. "
            "Tolerances as tight as ±0.2 mm."
        ),
        "unit_price": "45000.00",
        "available_materials": "PLA,PETG,ABS,Nylon",
        "published": True,
        "image_seeds": ["engineering", "mechanical", "prototype"],
    },
]

# Per-product feedback: {product_name: [(reviewer, rating, comment), ...]}
FEEDBACKS = {
    "Geometric Planter": [
        ("Alice M.",       5, "Absolutely stunning quality. The planter looks gorgeous on my windowsill!"),
        ("Jean-Paul N.",   5, "Shipped fast, colour was exactly as described. My succulents love it."),
        ("Diana K.",       4, "Beautiful design and solid build. A tiny rough edge on the bottom but minor."),
        ("Sophie R.",      5, "Bought three of these as gifts. Everyone was thrilled. Will reorder."),
        ("Martin B.",      4, "Great eco-friendly alternative to plastic pots. Very happy with the purchase."),
        ("Chloé F.",       5, "The honeycomb texture is even more striking in person. 10/10 recommend."),
    ],
    "Minimalist Phone Stand": [
        ("Grace U.",       5, "Sleek, sturdy, and the cable groove is genuinely useful. Love it."),
        ("Kevin L.",       4, "Exactly what a desk stand should be — minimal and functional."),
        ("Amara T.",       5, "The quality is way above what I expected for the price. Very impressed."),
        ("Patrick O.",     4, "Fits all my phones perfectly. Clean look on my desk."),
        ("Noor A.",        5, "Ordered for my home office setup. Couldn't be happier."),
        ("Yves D.",        4, "Solid and stable. The cable management detail is a nice touch."),
    ],
    "Articulated Dragon": [
        ("Diane R.",       5, "Print quality is incredible. Every segment moves perfectly off the printer!"),
        ("Samuel N.",      5, "Bought as a birthday gift. My nephew was absolutely blown away."),
        ("Fatima O.",      4, "Stunning collector's piece. The rainbow silk filament shimmering beautifully."),
        ("Eric B.",        5, "The detail on each segment is mind-blowing. Worth every franc."),
        ("Linda M.",       5, "Best 3D print I've ever owned. Poseable and display-worthy."),
        ("Thierry G.",     4, "Great quality. Took a couple of days to arrive but absolutely worth it."),
    ],
    "Custom Name Keychain": [
        ("Samuel N.",      5, "Ordered keychains for my whole team. Everyone loved them. Quick turnaround!"),
        ("Rita P.",        5, "Perfect personalised gift. The name came out razor-sharp."),
        ("Ben H.",         4, "Good quality for the price. Colours are vivid and it feels durable."),
        ("Julia W.",       5, "Ordered ten for a corporate event. Delivered on time, looked great."),
        ("James C.",       4, "Simple and well-made. Exactly as pictured."),
        ("Aisha L.",       5, "Gifted to my bridesmaids. They absolutely loved the personalisation."),
    ],
    "Wall-Mount Cable Organiser": [
        ("Grace U.",       4, "Tidy desk, happy me. These clips grip cables firmly without slipping."),
        ("Tom F.",         5, "Finally sorted my home-office cable nightmare. These are brilliant."),
        ("Olga S.",        4, "Very sturdy adhesive. Been on my wall for two months with no signs of falling."),
        ("Marcus J.",      5, "Bought two packs — they look clean and professional. Highly recommend."),
        ("Petra K.",       4, "Good product. Minor: the pack of 5 ran out fast so I ordered more."),
        ("Dominique A.",   5, "My standing desk setup is finally cable-free. Worth every shilling."),
    ],
    "Architectural Interior Render": [
        ("Jean-Pierre K.", 5, "The render helped us close a major client deal. Absolutely photorealistic."),
        ("Sara N.",        5, "Delivered in 4K, lighting was perfect. Our client couldn't believe it wasn't a photo."),
        ("Paul D.",        4, "Very high quality. A small tweak on material textures was handled quickly."),
        ("Lucia F.",       5, "We use Rwooga for all our project presentations now. Unbeatable quality."),
        ("Hassan A.",      5, "Turnaround was faster than promised and the renders were sensational."),
        ("Ingrid V.",      4, "Great service overall. The final images impressed our investors enormously."),
    ],
    "Product Showcase Render": [
        ("Fatima O.",      4, "Very happy with our product renders. Made our launch campaign much easier."),
        ("Leo B.",         5, "Studio-quality images without a single physical sample needed. Magic."),
        ("Anne M.",        5, "The 360-spin package was outstanding. Our e-commerce conversion improved."),
        ("Chris T.",       4, "High quality and quick delivery. Our team was very impressed."),
        ("Mei L.",         5, "The renders look better than our actual product photos. Incredible."),
        ("Stefan K.",      4, "Great value. We ordered additional angles after seeing the first batch."),
    ],
    "Product Commercial Animation": [
        ("Kevin T.",       5, "The animation perfectly captures our brand. Engagement tripled after launch."),
        ("Nina A.",        5, "The 30-second spot was polished, energetic, and on-brand. Exceptional."),
        ("Damien C.",      4, "A couple of revision rounds but the final output was worth it."),
        ("Olivia P.",      5, "Our TikTok ads have never performed better. Rwooga delivered."),
        ("Michael R.",     5, "Professional, fast, and creative. We'll be back for the 60-second version."),
        ("Yuki S.",        4, "Great collaboration process. The team was very responsive to feedback."),
    ],
    "Explainer Animation": [
        ("Samuel N.",      5, "The explainer video perfectly communicates our SaaS product. 10/10."),
        ("Brenda O.",      5, "Used it in our pitch deck. Investors said it was the clearest explainer they'd seen."),
        ("Thomas L.",      4, "Solid work. One revision cycle was all it took to get it right."),
        ("Amira K.",       5, "Excellent coordination from script to delivery. The result is outstanding."),
        ("Pierre N.",      4, "Very professional team and a high-quality end product."),
        ("Carmen V.",      5, "Our social media engagement skyrocketed after posting this. Highly recommend."),
    ],
    "Custom Figurine": [
        ("Eric B.",        5, "Fastest turnaround I've seen. The figurine looks just like my daughter!"),
        ("Sandra G.",      5, "Ordered as a wedding gift — the couple was moved to tears. Stunning detail."),
        ("Kwame A.",       4, "Incredible resin quality. The paint finish could be slightly more even but still beautiful."),
        ("Naomi H.",       5, "My portrait figurine is the talk of the office. Everyone wants one!"),
        ("Felix M.",       5, "The 20 cm version is a showpiece. Absolutely lifelike. Worth every franc."),
        ("Chiara B.",      4, "Great craftsmanship, packaging was excellent, delivered safely."),
    ],
    "Mechanical Part Prototyping": [
        ("Marco R.",       5, "The tolerance on our bracket was within ±0.1 mm. Remarkable precision."),
        ("Laura T.",       5, "Saved our production line with a replacement part printed overnight."),
        ("David S.",       4, "Good communication throughout. The Nylon part we ordered is very strong."),
        ("Fatoumata D.",  5, "The CAD model was created from just a rough sketch. Highly professional."),
        ("Andreas K.",     4, "Second order with Rwooga. Consistently reliable quality and fast delivery."),
        ("Beatrice N.",    5, "Perfect fit for our enclosure. Will be using Rwooga for all prototyping going forward."),
    ],
}

# 800×600 Picsum image — unique per seed word
PICSUM_URL = "https://picsum.photos/seed/{seed}/800/600"


def download_image(seed: str) -> tuple[bytes, str]:
    """Download a deterministic placeholder image from Picsum Photos."""
    url = PICSUM_URL.format(seed=seed)
    resp = requests.get(url, timeout=15)
    resp.raise_for_status()
    content_type = resp.headers.get("Content-Type", "image/jpeg")
    ext = "jpg" if "jpeg" in content_type else content_type.split("/")[-1]
    return resp.content, ext


class Command(BaseCommand):
    help = "Seed the database with sample categories, products, images (via Cloudinary), and reviews"

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Wipe existing products and categories before seeding",
        )
        parser.add_argument(
            "--no-images",
            action="store_true",
            help="Skip image download/upload (useful for quick re-seeds)",
        )

    def handle(self, *args, **options):
        skip_images = options["no_images"]

        if options["clear"]:
            self.stdout.write("🗑  Clearing existing data...")
            Product.objects.all().delete()
            ServiceCategory.objects.all().delete()
            Discount.objects.all().delete()

        # ── 1. Service categories ─────────────────────────────────────────────
        self.stdout.write("\n📂 Creating service categories...")
        cat_map = {}
        for cat_data in CATEGORIES:
            cat, created = ServiceCategory.objects.get_or_create(
                name=cat_data["name"],
                defaults={
                    "requires_dimensions": cat_data["requires_dimensions"],
                    "requires_material": cat_data["requires_material"],
                    "is_active": cat_data["is_active"],
                },
            )
            cat_map[cat.name] = cat
            label = "✅ Created" if created else "⏭  Exists"
            self.stdout.write(f"  {label}: {cat.name}")

        # ── 2. Sample discount ────────────────────────────────────────────────
        discount, _ = Discount.objects.get_or_create(
            name="Launch Sale 10%",
            defaults={
                "discount_type": Discount.PERCENTAGE,
                "discount_value": 10,
                "start_date": timezone.now(),
                "end_date": timezone.now() + timezone.timedelta(days=30),
                "is_active": True,
            },
        )

        # ── 3. Products + images ──────────────────────────────────────────────
        self.stdout.write("\n📦 Creating products...")
        products_created = []

        for p_data in PRODUCTS:
            cat = cat_map.get(p_data["category"])
            if not cat:
                self.stdout.write(self.style.WARNING(f"  ⚠️  Unknown category '{p_data['category']}' — skip"))
                continue

            product, created = Product.objects.get_or_create(
                name=p_data["name"],
                defaults={
                    "category": cat,
                    "short_description": p_data["short_description"],
                    "detailed_description": p_data.get("detailed_description", ""),
                    "unit_price": p_data.get("unit_price"),
                    "currency": "RWF",
                    "length": p_data.get("length"),
                    "width": p_data.get("width"),
                    "height": p_data.get("height"),
                    "available_sizes": p_data.get("available_sizes", ""),
                    "available_colors": p_data.get("available_colors", ""),
                    "available_materials": p_data.get("available_materials", ""),
                    "published": p_data.get("published", True),
                },
            )
            products_created.append(product)
            price_str = f" — RWF {int(float(product.unit_price)):,}" if product.unit_price else ""
            label = "✅ Created" if created else "⏭  Exists"
            self.stdout.write(f"  {label}: {product.name}{price_str}")

            # Attach discount to first 3 products
            if created and len(products_created) <= 3:
                ProductDiscount.objects.get_or_create(product=product, discount=discount)

            # ── Upload images ─────────────────────────────────────────────────
            if skip_images:
                continue

            # Only add images if none exist for this product yet
            if product.product_media.exists():
                self.stdout.write(f"    🖼  Images already exist — skipping upload")
                continue

            image_seeds = p_data.get("image_seeds", [p_data["name"].lower().replace(" ", "-")])
            for idx, seed in enumerate(image_seeds):
                try:
                    self.stdout.write(f"    ⬇️  Downloading image [{seed}]...")
                    img_bytes, ext = download_image(seed)
                    filename = f"{product.slug}-{idx + 1}.{ext}"
                    media = ProductMedia(
                        product=product,
                        alt_text=f"{product.name} — view {idx + 1}",
                        display_order=idx,
                    )
                    media.image.save(filename, ContentFile(img_bytes), save=True)
                    self.stdout.write(self.style.SUCCESS(f"    ☁️  Uploaded: {filename}"))
                except Exception as exc:
                    self.stdout.write(self.style.ERROR(f"    ❌ Failed [{seed}]: {exc}"))

        # ── 4. Feedback — 5+ per product ──────────────────────────────────────
        self.stdout.write("\n⭐ Adding sample feedback (5+ per product)...")
        for product_name, reviews in FEEDBACKS.items():
            try:
                product = Product.objects.get(name=product_name)
            except Product.DoesNotExist:
                self.stdout.write(self.style.WARNING(f"  ⚠️  Product not found: {product_name}"))
                continue
            for name, rating, message in reviews:
                fb, created = Feedback.objects.get_or_create(
                    product=product,
                    client_name=name,
                    defaults={"message": message, "rating": rating, "published": True},
                )
                if created:
                    self.stdout.write(f"  ⭐ {rating}/5 on '{product.name}' from {name}")

        # ── Summary ───────────────────────────────────────────────────────────
        total_media = ProductMedia.objects.count()
        self.stdout.write(self.style.SUCCESS(
            f"\n🎉 Done! "
            f"{ServiceCategory.objects.count()} categories, "
            f"{Product.objects.count()} products, "
            f"{total_media} images, "
            f"{Feedback.objects.count()} reviews seeded."
        ))
