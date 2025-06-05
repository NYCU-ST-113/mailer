# Mailer Service

This repository contains the Mailer Service, a microservice designed to handle email sending operations for the classroom booking system.

## Overview

The Mailer Service provides a reliable way to send emails using SMTP, with support for email templates and attachments. It's built with FastAPI and designed to work as part of a microservices architecture.

## Getting Started

Follow these steps to set up and run the Mailer Service on your local machine.

### Prerequisites

- Python 3.8 or higher
- pip (Python package installer)
- SMTP server access (for sending emails)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd mailer
   ```

2. **Create and activate a virtual environment**
   ```bash
   # Create a virtual environment
   python3 -m venv mailer_env
   
   # Activate the virtual environment
   # On Linux/Mac:
   source mailer_env/bin/activate
   
   # On Windows:
   # mailer_env\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Create necessary directories**
   ```bash
   mkdir -p logs csv_exports
   ```

5. **Set up environment variables**
   
   Create a `.env` file in the root directory with the following variables:
   ```
   SMTP_SERVER=<your-smtp-server>
   SMTP_PORT=<smtp-port>
   SMTP_USERNAME=<your-username>
   SMTP_PASSWORD=<your-password>
   SENDER_EMAIL=<sender-email-address>
   ```

### Running the Service

Start the Mailer Service with:

```bash
uvicorn mailer_service.main:app --reload --port 6000
```

The service will be available at `http://localhost:6000`.

## API Documentation

Once the service is running, you can access the API documentation at:
- Swagger UI: `http://localhost:6000/docs`
- ReDoc: `http://localhost:6000/redoc`

## Features

- Send plain text and HTML emails
- Support for email templates

## Testing

Run the tests with:

```bash
python3 -m pytest test/test_mailer.py -v
```

For coverage report:
```bash
python3 -m pytest --cov=mailer_service --cov-report=term-missing test/
```

## Project Structure

```
mailer/
├── common_utils/      
│   ├── common_utils
│   │   ├── logger
│   │       ├── __init__.py
│   │       ├── client.py # client api for calling logger micro-service
│   │   ├── mailer
│   │       ├── __init__.py
│   │       ├── client.py # client api for calling mailer micro-service
│   ├── setup.py               
├── mailer_service/       # Main package
│   ├── __init__.py
│   ├── main.py           # FastAPI application
│   ├── templates/        # Email templates
├── tests/                # Test package
│   ├── __init__.py
│   └── test_mailer.py    # Tests for mailer service
├── .env                  # Environment variables (for mailtrap, not in repo)
├── .gitignore            # Git ignore file
├── requirements.txt      # Project dependencies
└── README.md             # This file
```

## Notes

- This service was originally part of a larger microservices architecture including Payment Service and Logger Service, which have been removed to make this a standalone service.
- When integrating with other services, you may need to adjust configurations accordingly.

## License


## Contact
