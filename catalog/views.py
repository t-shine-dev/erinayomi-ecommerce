from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.core.paginator import Paginator
from django.db.models import Avg, Count, Prefetch, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from store_settings.models import StoreSettings
from wishlist.utils import get_wishlist_ids

from .models import Category, Product, Review, TailoringAppointment
from .services import send_tailoring_notification


def home(request):
    active = (
        Product.objects.filter(is_active=True)
        .select_related("category")
        .prefetch_related("images")
        .annotate(avg_rating_annotated=Avg("reviews__rating"), review_count_annotated=Count("reviews", distinct=True))
    )

    featured = active.filter(is_featured=True)[:8]
    if not featured.exists():
        featured = active[:8]

    best_sellers = active.order_by("-review_count_annotated", "-created_at")[:4]
    new_arrivals = active.order_by("-created_at")[:4]
    flash_sales = active.filter(discount_price__isnull=False).order_by("-created_at")[:4]
    luxury_collection = active.order_by("-price")[:4]
    categories = Category.objects.prefetch_related(
        Prefetch(
            "products",
            queryset=Product.objects.filter(is_active=True).prefetch_related("images"),
            to_attr="active_products",
        )
    )
    tailoring_products = active.filter(product_type=Product.ProductType.TAILORING)[:4]

    real_reviews = (
        Review.objects.filter(rating__gte=4)
        .exclude(comment="")
        .select_related("user", "product")
        .order_by("-rating", "-created_at")[:6]
    )

    context = {
        "featured": featured,
        "best_sellers": best_sellers,
        "new_arrivals": new_arrivals,
        "flash_sales": flash_sales,
        "luxury_collection": luxury_collection,
        "categories": categories,
        "tailoring_products": tailoring_products,
        "real_reviews": real_reviews,
        "wishlist_ids": get_wishlist_ids(request),
    }
    return render(request, "catalog/home.html", context)


def product_list(request):
    products = (
        Product.objects.filter(is_active=True)
        .select_related("category")
        .prefetch_related("images")
        .annotate(
            avg_rating_annotated=Avg("reviews__rating"),
            review_count_annotated=Count("reviews", distinct=True),
        )
    )

    query = request.GET.get("q", "").strip()
    category_slugs = request.GET.getlist("category")
    product_type = request.GET.get("type", "")
    sort = request.GET.get("sort", "")
    min_price = request.GET.get("min_price", "").strip()
    max_price = request.GET.get("max_price", "").strip()
    min_rating = request.GET.get("min_rating", "").strip()
    availability = request.GET.get("availability", "")
    new_only = request.GET.get("new", "")

    if query:
        products = products.filter(
            Q(name__icontains=query) | Q(description__icontains=query) | Q(sku__icontains=query)
        )
    if category_slugs:
        products = products.filter(category__slug__in=category_slugs)
    if product_type:
        products = products.filter(product_type=product_type)
    if min_price.isdigit():
        products = products.filter(price__gte=int(min_price))
    if max_price.isdigit():
        products = products.filter(price__lte=int(max_price))
    if min_rating.isdigit():
        products = products.filter(avg_rating_annotated=int(min_rating))
    if availability == "in_stock":
        products = products.filter(stock__gt=0)
    elif availability == "out_of_stock":
        products = products.filter(stock=0)
    if new_only:
        import datetime

        from django.utils import timezone

        products = products.filter(created_at__gte=timezone.now() - datetime.timedelta(days=14))

    sort_map = {
        "price_asc": "price",
        "price_desc": "-price",
        "newest": "-created_at",
        "name": "name",
        "rating": "-avg_rating_annotated",
    }
    products = products.order_by(sort_map.get(sort, "-created_at"))

    paginator = Paginator(products, 12)
    page_obj = paginator.get_page(request.GET.get("page"))

    qs = request.GET.copy()
    qs.pop("page", None)
    base_qs = (qs.urlencode() + "&") if qs else ""

    context = {
        "page_obj": page_obj,
        "base_qs": base_qs,
        "categories": Category.objects.all(),
        "product_types": Product.ProductType.choices,
        "query": query,
        "selected_categories": category_slugs,
        "selected_type": product_type,
        "selected_sort": sort,
        "min_price": min_price,
        "max_price": max_price,
        "min_rating": min_rating,
        "availability": availability,
        "new_only": new_only,
        "wishlist_ids": get_wishlist_ids(request),
    }
    return render(request, "catalog/product_list.html", context)


RECENTLY_VIEWED_SESSION_KEY = "recently_viewed_product_ids"
RECENTLY_VIEWED_MAX = 8


def _track_recently_viewed(request, product_id):
    ids = request.session.get(RECENTLY_VIEWED_SESSION_KEY, [])
    ids = [i for i in ids if i != product_id]
    ids.insert(0, product_id)
    request.session[RECENTLY_VIEWED_SESSION_KEY] = ids[:RECENTLY_VIEWED_MAX]


def product_detail(request, slug):
    product = get_object_or_404(
        Product.objects.select_related("category").prefetch_related("images", "reviews__user"),
        slug=slug,
        is_active=True,
    )
    related = (
        Product.objects.filter(category=product.category, is_active=True)
        .exclude(pk=product.pk)
        .prefetch_related("images")
        .annotate(avg_rating_annotated=Avg("reviews__rating"), review_count_annotated=Count("reviews", distinct=True))
        [:4]
    )
    user_has_reviewed = (
        request.user.is_authenticated
        and product.reviews.filter(user=request.user).exists()
    )

    recently_viewed_ids = [
        i for i in request.session.get(RECENTLY_VIEWED_SESSION_KEY, []) if i != product.id
    ]
    recently_viewed = []
    if recently_viewed_ids:
        products_by_id = Product.objects.filter(id__in=recently_viewed_ids).prefetch_related("images").annotate(
            avg_rating_annotated=Avg("reviews__rating"), review_count_annotated=Count("reviews", distinct=True)
        ).in_bulk()
        recently_viewed = [
            products_by_id[i] for i in recently_viewed_ids
            if i in products_by_id and products_by_id[i].is_active
        ][:4]

    _track_recently_viewed(request, product.id)

    context = {
        "product": product,
        "related": related,
        "user_has_reviewed": user_has_reviewed,
        "rating_range": range(1, 6),
        "wishlist_ids": get_wishlist_ids(request),
        "recently_viewed": recently_viewed,
    }
    return render(request, "catalog/product_detail.html", context)


@login_required
def add_review(request, slug):
    product = get_object_or_404(Product, slug=slug, is_active=True)
    if request.method == "POST":
        rating = request.POST.get("rating")
        comment = request.POST.get("comment", "").strip()
        if not rating or not rating.isdigit() or not (1 <= int(rating) <= 5):
            messages.error(request, "Please choose a rating between 1 and 5.")
        elif Review.objects.filter(product=product, user=request.user).exists():
            messages.error(request, "You've already reviewed this product.")
        else:
            Review.objects.create(
                product=product, user=request.user, rating=int(rating), comment=comment
            )
            messages.success(request, "Thanks for your review!")
    return redirect("catalog:product_detail", slug=slug)


def contact(request):
    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        email = request.POST.get("email", "").strip()
        message_body = request.POST.get("message", "").strip()

        if not all([name, email, message_body]):
            messages.error(request, "Please fill in every field before sending.")
        else:
            store_email = StoreSettings.load().business_email or settings.DEFAULT_STORE_EMAIL
            try:
                send_mail(
                    subject=f"New contact form message from {name}",
                    message=f"From: {name} <{email}>\n\n{message_body}",
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[store_email],
                    fail_silently=True,
                )
            except Exception:
                pass
            messages.success(request, "Thanks for reaching out — we'll get back to you shortly.")
        return redirect("catalog:contact")

    return render(request, "catalog/contact.html")


def about(request):
    return render(request, "catalog/about.html")


def tailoring(request):
    if request.method == "POST":
        full_name = request.POST.get("full_name", "").strip()
        email = request.POST.get("email", "").strip()
        phone_number = request.POST.get("phone_number", "").strip()
        service_type = request.POST.get("service_type", "")
        preferred_date = request.POST.get("preferred_date") or None
        preferred_time = request.POST.get("preferred_time", "").strip()
        completion_date = request.POST.get("completion_date") or None
        measurements_notes = request.POST.get("measurements_notes", "").strip()
        reference_notes = request.POST.get("reference_notes", "").strip()
        inspiration_image = request.FILES.get("inspiration_image")

        def _decimal(field_name):
            raw = request.POST.get(field_name, "").strip()
            try:
                return float(raw) if raw else None
            except ValueError:
                return None

        measurement_fields = {
            "measurement_chest": _decimal("measurement_chest"),
            "measurement_waist": _decimal("measurement_waist"),
            "measurement_hip": _decimal("measurement_hip"),
            "measurement_shoulder": _decimal("measurement_shoulder"),
            "measurement_sleeve": _decimal("measurement_sleeve"),
            "measurement_length": _decimal("measurement_length"),
        }

        if not all([full_name, email, phone_number, service_type]):
            messages.error(request, "Please fill in your name, email, phone, and service type.")
        else:
            appointment = TailoringAppointment.objects.create(
                full_name=full_name,
                email=email,
                phone_number=phone_number,
                service_type=service_type,
                preferred_date=preferred_date,
                preferred_time=preferred_time,
                completion_date=completion_date,
                inspiration_image=inspiration_image,
                measurements_notes=measurements_notes,
                reference_notes=reference_notes,
                **measurement_fields,
            )
            send_tailoring_notification(appointment)
            messages.success(
                request,
                "Your tailoring appointment request has been received — we'll confirm your slot by phone or email shortly.",
            )
        return redirect("catalog:tailoring")

    portfolio = Product.objects.filter(
        is_active=True, product_type=Product.ProductType.TAILORING
    ).prefetch_related("images")[:8]
    context = {
        "portfolio": portfolio,
        "service_types": TailoringAppointment.ServiceType.choices,
    }
    return render(request, "catalog/tailoring.html", context)


def search_suggestions(request):
    query = request.GET.get("q", "").strip()
    results = []
    if len(query) >= 2:
        products = (
            Product.objects.filter(is_active=True)
            .filter(Q(name__icontains=query) | Q(sku__icontains=query))
            .select_related("category")
            .prefetch_related("images")[:6]
        )
        for p in products:
            img = p.primary_image
            results.append(
                {
                    "name": p.name,
                    "url": p.get_absolute_url(),
                    "price": f"₦{p.current_price:,.0f}",
                    "image": img.image.url if img else "",
                    "category": p.get_product_type_display(),
                }
            )
    return JsonResponse({"results": results})
