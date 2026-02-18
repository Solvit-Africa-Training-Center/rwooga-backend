# rwooga-backend

Backend API for Rwooga 3D services and portfolio website.

## Project Overview
This is a Django-based web application designed to manage accounts, orders, pricing, products, and utilities. The project is structured into multiple apps to ensure modularity and scalability.

## Features
- **Accounts**: Manage user authentication and profiles.
- **Orders**: Handle order creation, updates, and tracking.
- **Products**: Manage product catalog and inventory.
- **Utilities**: Shared utilities and helper functions.

## Project Structure
```
Project Structure
rwooga_backend/
│
├── accounts/          # Authentication & user profiles
│   ├── models.py
│   ├── serializers.py
│   ├── permissions.py
│   ├── views.py
│   ├── urls.py
│
├── products/           # Products & categories
│   ├── models.py
│   ├── serializers.py
│   ├── views.py
│   ├── urls.py
│
├── orders/              # Shopping cart logic
│   ├── models.py
│   ├── serializers.py
│   ├── views.py
│
├── rwoogaBackend/  # Project settings
│   ├── settings.py
│   ├── urls.py               # URLs Routing
├── utils/             
│   ├──                    # Email and Verification Code Sending
│   ├── 
│   ├── 
├── .env                     # Environment variables 
├── .gitignore
├── requirements.txt        # Dependencies
└── manage.py
```
- `manage.py`: Django's command-line utility for administrative tasks.
- `requirements.txt`: Lists the Python dependencies for the project.
- `rwooga/`: Contains project-wide settings and configurations.
- Each app folder (e.g., `accounts/`, `orders/`) contains:
  - `models.py`: Database models.
  - `views.py`: Application logic.
  - `tests.py`: Unit tests.
  - `admin.py`: Admin panel configurations.

## Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/Solvit-Africa-Training-Center/rwooga-backend.git
   ```
2. Navigate to the project directory:
   ```bash
   cd capstone
   ```
3. Create and activate a virtual environment:
   ```bash
   python -m venv env
   source env/bin/activate # On Windows: env\Scripts\activate
   ```
4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
5. Apply migrations:
   ```bash
   python manage.py migrate
   ```
6. Run the development server:
   ```bash
   python manage.py runserver
   ```

## Usage
- Access the application at `http://127.0.0.1:8000/`.
- Use the Django admin panel at `http://127.0.0.1:8000/admin/` for administrative tasks.

## Contributing
1. Fork the repository.
2. Create a new branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. Commit your changes:
   ```bash
   git commit -m "Add your message here"
   ```
4. Push to your branch:
   ```bash
   git push origin feature/your-feature-name
   ```
5. Open a pull request.

**Note:** Do not push directly to the `main` branch. Always create a new branch for your changes and submit a pull request for review.

## License
This project is licensed under the MIT License. See the LICENSE file for details.

## Acknowledgments
- Django documentation: [https://docs.djangoproject.com/](https://docs.djangoproject.com/)
- Python documentation: [https://docs.python.org/](https://docs.python.org/)
