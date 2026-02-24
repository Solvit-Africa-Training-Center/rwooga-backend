# rwooga-backend

Backend API for Rwooga 3D services and portfolio website.

## Project Overview

Django REST Framework API managing accounts, orders, payments, products, returns/refunds, and email utilities for the Rwooga platform.

## Features

- **Accounts** — JWT auth, email verification, password reset, user profiles
- **Orders** — Order lifecycle, return requests, refund tracking
- **Payments** — MTN MoMo (Paypack) and card payment processing
- **Products** — Product catalog, categories, discounts, wishlists, feedback, custom-request control
- **Utils** — Shared email sending and verification helpers

## Project Structure

```
rwooga-backend/
│
├── accounts/                        # Authentication & user management
│   ├── admin.py
│   ├── models.py                    # CustomUser model
│   ├── serializers.py               # Register, login, profile serializers
│   ├── permissions.py               # Custom DRF permission classes
│   ├── signals.py                   # Post-save signals
│   ├── validators.py                # Field validators
│   ├── views.py                     # Register, login, verify, reset-password
│   ├── urls.py
│   └── migrations/
│
├── orders/                          # Orders, Returns & Refunds
│   ├── admin.py
│   ├── models.py                    # Order, OrderItem, Return, Refund
│   ├── serializers.py               # Serializers + approve/reject/complete actions
│   ├── views.py                     # OrderViewSet, ReturnViewSet, RefundViewSet
│   ├── urls.py
│   └── migrations/
│       ├── 0001_initial.py
│       └── 0002_refund_return.py
│
├── payments/                        # Payment processing
│   ├── admin.py
│   ├── models.py                    # Payment model (MoMo, Card, status tracking)
│   ├── serializers.py
│   ├── paypack_utils.py             # Paypack MoMo API helpers
│   ├── views.py                     # Initiate, cancel, verify, webhook
│   ├── urls.py
│   └── migrations/
│
├── products/                        # Product catalog & related features
│   ├── admin.py
│   ├── models.py                    # Product, ServiceCategory, ProductDiscount,
│   │                                #   Feedback, Wishlist, WishlistItem,
│   │                                #   ControlRequest
│   ├── serializers.py
│   ├── permissions.py
│   ├── views.py                     # Products, Categories, Discounts,
│   │                                #   Wishlist, Feedback, ControlRequest
│   ├── urls.py
│   ├── management/
│   │   └── commands/
│   │       └── seed_products.py     # Seed sample products command
│   └── migrations/
│
├── utils/                           # Shared email & verification utilities
│   ├── models.py
│   ├── views.py
│   ├── send_email.py                # Base email sending helper
│   ├── registration_verification.py # Sends signup verification code
│   ├── password_reset_verification.py # Sends password reset code
│   └── email_change_verification.py   # Sends email change confirmation
│
├── rwoogaBackend/                   # Django project configuration
│   ├── settings.py
│   ├── urls.py                      # Root URL dispatcher
│   ├── asgi.py
│   └── wsgi.py
│
├── templates/                       # Django HTML templates
├── static/                          # Static source files
├── staticfiles/                     # Collected static (production)
├── media/                           # User-uploaded media
│
├── Dockerfile                       # Container build instructions
├── Procfile                         # Process commands (Koyeb/Heroku)
├── start.sh                         # Server startup script
├── runtime.txt                      # Python version pin
├── requirements.txt                 # Python dependencies
├── manage.py
└── .env                             # Environment variables (not committed)
```

## API Endpoints Summary

| App | Base Path | Description |
|---|---|---|
| accounts | `/api/v1/auth/` | Register, login, refresh, verify, reset password |
| orders | `/api/v1/orders/orders/` | Order CRUD |
| orders | `/api/v1/orders/returns/` | Return requests + approve/reject/complete/cancel |
| orders | `/api/v1/orders/refunds/` | Refund tracking + complete/fail |
| payments | `/api/v1/payments/` | Initiate & manage payments |
| products | `/api/v1/products/` | Products, categories, discounts, wishlist, feedback |

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/mambatheo/rwooga-DjangoBackend.git
   cd rwooga-backend
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv env
   env\Scripts\activate   # Windows
   source env/bin/activate  # macOS/Linux
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Copy `.env.example` to `.env` and fill in your values.

5. Apply migrations:
   ```bash
   python manage.py migrate
   ```

6. (Optional) Seed sample products:
   ```bash
   python manage.py seed_products
   ```

7. Run the development server:
   ```bash
   python manage.py runserver
   ```

## Usage

- API root: `http://127.0.0.1:8000/api/v1/`
- Swagger docs: `http://127.0.0.1:8000/api/docs/`
- Django admin: `http://127.0.0.1:8000/admin/`

## Contributing

1. Fork the repository.
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Commit your changes: `git commit -m "feat: describe your change"`
4. Push and open a pull request.

> **Note:** Do not push directly to `main`. Always submit a pull request for review.

