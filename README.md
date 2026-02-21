## Project Structure

```
rwooga_backend/
│
├── accounts/              # Authentication & user profiles
│   ├── models.py
│   ├── serializers.py
│   ├── permissions.py
│   ├── views.py
│   ├── urls.py
│
├── products/              # Products & categories
│   ├── models.py
│   ├── serializers.py
│   ├── views.py
│   ├── urls.py
│
├── orders/                # Shopping cart logic
│   ├── models.py
│   ├── serializers.py
│   ├── views.py
│
├── pricing/               # Product discount control
│   ├── models.py
│   ├── serializers.py
│   ├── views.py
│
├── utils/                 # Email & verification utilities
│   ├── email_service.py
│   ├── verification.py
│
├── static/                # Static files
│
├── rwooga/                # Project settings
│   ├── settings.py
│   ├── urls.py
│
├── .env                   # Environment variables
├── .gitignore
├── requirements.txt       # Dependencies
└── manage.py
```
