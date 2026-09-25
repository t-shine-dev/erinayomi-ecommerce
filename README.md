# ERINAYOMI E-Commerce Platform

A full-stack Django e-commerce platform built for **ERINAYOMI**, a fashion and accessories business specializing in jewelry, rings, watches, tailoring, and fashion accessories.

The project was built to provide a complete online shopping experience including customer authentication, product browsing, live search, cart management, wishlist functionality, checkout, Paystack payments, order tracking, customer profiles, reviews, and an administrative dashboard.

---

## ✨ Features

### 🛍️ Storefront
- Responsive luxury-focused storefront design
- Product categories
- Featured products
- Product detail pages
- Product image management
- Product stock management
- Sale pricing
- Product reviews
- Related products

### 🔎 Live Product Search
- Search products without leaving the current page
- Live auto-suggest search
- Search results update dynamically using JavaScript Fetch API
- Product filtering by category and search terms

### 👤 Customer Accounts
- User registration and authentication
- Login and logout
- Customer profile management
- Editable first and last name
- Email and phone number management
- Shipping address management
- Password change functionality
- Customer order history
- Custom profile/navigation icon

### ❤️ Wishlist
- Add products to wishlist
- Remove products from wishlist
- View saved products
- Wishlist count displayed in navigation

### 🛒 Shopping Cart
- Add products to cart
- Update product quantities
- Remove products
- Cart total calculation
- Support for both guest and authenticated customers

### 💳 Checkout & Payments
- Customer checkout
- Order creation
- Paystack payment integration
- Server-side transaction verification
- Payment status tracking
- Paystack webhook support
- Order numbers generated for customers

### 📦 Orders
- Order history
- Order detail pages
- Order status tracking
- Customer order information
- Admin order management

### 🏠 Tailoring
- Dedicated tailoring section
- Tailoring appointment functionality
- Customer information collection for tailoring requests

### ⚙️ Admin Dashboard
- Product management
- Category management
- Order management
- Customer management
- Review management
- Store settings
- Business contact information
- Social media links
- Logo management

### 🎨 Store Settings
Business information can be managed from the admin dashboard, including:

- Business name
- Email address
- Phone number
- WhatsApp contact
- Business address
- Operating hours
- Social media links
- Store logo

These settings can then be displayed throughout the storefront.

---

# 🧰 Tech Stack

### Backend
- **Python**
- **Django**
- **Django REST Framework**
- Django Authentication
- Django ORM

### Database
- **PostgreSQL** — recommended for production
- **SQLite** — available for local development

### Frontend
- **HTML5**
- **Tailwind CSS**
- **Bootstrap**
- **CSS**
- **JavaScript**
- **Fetch API**
- Responsive design

### Payments & Services
- **Paystack** — payment processing
- **Cloudinary** — optional cloud media storage
- **WhiteNoise** — static file serving
- **Gunicorn** — production WSGI server

---

# 📁 Project Structure

```text
erinayomi/
│
├── erinayomi/
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
│
├── accounts/
│   └── Customer authentication,
│       profiles, addresses and account settings
│
├── catalog/
│   └── Products, categories, reviews
│       and product search
│
├── cart/
│   └── Shopping cart functionality
│
├── orders/
│   └── Orders, order items and checkout
│
├── payments/
│   └── Paystack payment integration
│
├── wishlist/
│   └── Customer wishlist functionality
│
├── store_settings/
│   └── Business information and
│       storefront settings
│
├── templates/
│   ├── base.html
│   ├── accounts/
│   ├── catalog/
│   ├── cart/
│   ├── orders/
│   ├── payments/
│   ├── wishlist/
│   └── partials/
│
├── static/
│   ├── css/
│   ├── js/
│   └── images/
│
├── media/
│   └── Uploaded product and store images
│
├── manage.py
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

---

# 🚀 Getting Started

## 1. Clone the Repository

```bash
git clone https://github.com/t-shine-dev/erinayomi.git
cd erinayomi
```

---

## 2. Create a Virtual Environment

```bash
python -m venv venv
```

### Git Bash

```bash
source venv/Scripts/activate
```

### Windows PowerShell

```powershell
venv\Scripts\Activate.ps1
```

---

## 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 4. Configure Environment Variables

Create a `.env` file from the example:

### Git Bash

```bash
cp .env.example .env
```

Open `.env` and configure the required values.

Example:

```env
SECRET_KEY=your-secret-key
DEBUG=True

DATABASE_URL=

PAYSTACK_PUBLIC_KEY=your-paystack-public-key
PAYSTACK_SECRET_KEY=your-paystack-secret-key
```

For local development, leaving `DATABASE_URL` empty allows the project to use SQLite if your Django settings are configured for that fallback.

---

# 🗄️ Database Setup

Run Django migrations:

```bash
python manage.py migrate
```

Create an administrator account:

```bash
python manage.py createsuperuser
```

Follow the prompts to create your admin account.

---

# ▶️ Run the Development Server

```bash
python manage.py runserver
```

The application will be available at:

```text
http://127.0.0.1:8000/
```

Admin dashboard:

```text
http://127.0.0.1:8000/admin/
```

---

# ⚙️ Initial Admin Setup

After logging into the Django admin dashboard:

### 1. Configure Store Settings

Add the business information used throughout the website:

- Business name
- Email
- Phone number
- WhatsApp number
- Address
- Operating hours
- Social media links
- Store logo

### 2. Create Categories

Examples:

- Rings
- Watches
- Necklaces
- Accessories
- Tailoring

### 3. Add Products

Each product can contain information such as:

- Product name
- Description
- Price
- Sale price
- Stock
- SKU
- Category
- Product image
- Featured status

### 4. Configure Featured Products

Products marked as featured can be displayed in the storefront's featured product sections.

---

# 💳 Paystack Integration

ERINAYOMI uses **Paystack** for online payment processing.

The checkout process works approximately as follows:

```text
Customer
   ↓
Add Products
   ↓
Shopping Cart
   ↓
Checkout
   ↓
Create Order
   ↓
Initialize Paystack Payment
   ↓
Paystack Checkout
   ↓
Customer Completes Payment
   ↓
Server-Side Verification
   ↓
Order Marked as Paid
```

The application verifies transactions with Paystack before treating an order as successfully paid.

For local testing, use Paystack test credentials and test payment details.

### Webhook

The project also supports a Paystack webhook for payment events.

Configure the webhook URL on your Paystack dashboard:

```text
https://your-domain.com/payments/webhook/
```

---

# ☁️ Cloudinary Media Storage

The project supports Cloudinary as an optional media storage solution.

During local development, uploaded files can be stored in:

```text
media/
```

For production, Cloudinary can be configured through environment variables.

Example:

```env
USE_CLOUDINARY=True
CLOUDINARY_URL=cloudinary://API_KEY:API_SECRET@CLOUD_NAME
```

---

# 🔐 Security

The project uses several Django security features and production practices, including:

- Environment variables for sensitive configuration
- Django authentication
- CSRF protection
- Password hashing
- Server-side payment verification
- Configurable `DEBUG`
- Configurable `ALLOWED_HOSTS`
- Secure production deployment configuration

Sensitive values such as secret keys and payment credentials should never be committed to GitHub.

---

# 🚀 Production Deployment

Before deploying the project:

### Set production environment variables

```env
DEBUG=False
SECRET_KEY=your-production-secret-key
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
DATABASE_URL=your-postgresql-database-url
```

### Collect static files

```bash
python manage.py collectstatic
```

### Run with Gunicorn

```bash
gunicorn erinayomi.wsgi:application
```

A production deployment should also use HTTPS and properly configured database, media storage, environment variables, and allowed hosts.

---

# 🧪 Development

Run Django's system checks:

```bash
python manage.py check
```

Run migrations:

```bash
python manage.py makemigrations
python manage.py migrate
```

Start the development server:

```bash
python manage.py runserver
```

---

# 📌 Main Django Applications

| App | Responsibility |
|---|---|
| `accounts` | Authentication, profiles and addresses |
| `catalog` | Products, categories and reviews |
| `cart` | Shopping cart |
| `orders` | Orders and checkout |
| `payments` | Paystack integration |
| `wishlist` | Customer wishlist |
| `store_settings` | Business/store configuration |

---

# 🎯 Project Goals

ERINAYOMI was developed as a practical full-stack Django project with a focus on:

- Building a real-world e-commerce workflow
- Working with Django models and relationships
- Authentication and user management
- PostgreSQL database integration
- REST API development
- Payment gateway integration
- Dynamic JavaScript interactions
- Responsive frontend development
- Admin dashboard functionality
- Production-oriented deployment practices

---

# 📚 What This Project Demonstrates

This project demonstrates practical experience with:

```text
Python
   ↓
Django
   ↓
Django ORM
   ↓
PostgreSQL
   ↓
Django REST Framework
   ↓
JavaScript / Fetch API
   ↓
Tailwind CSS
   ↓
Paystack API
   ↓
Cloudinary
   ↓
Git & GitHub
   ↓
Production Deployment
```

---

# 👨🏽‍💻 Author

**T Shine**

Backend Developer focused on:

- Python
- Django
- PostgreSQL
- Django REST Framework
- Git & GitHub

GitHub:

**[@t-shine-dev](https://github.com/t-shine-dev)**

---

# 📄 License

This project was created for the ERINAYOMI business and as part of my backend development portfolio.
