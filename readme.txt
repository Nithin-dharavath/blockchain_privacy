================================================================================
BLOCKCHAIN PRIVACY PLATFORM - Setup & Execution Guide
================================================================================

PROJECT OVERVIEW:
This is a Django-based privacy research platform that runs real cryptographic 
privacy experiments across five privacy-preserving techniques: Ring Signatures, 
Zero-Knowledge Proofs (ZKP), Secure Multi-Party Computation (SMPC), Trusted 
Execution Environments (TEE), and Cryptocurrency Mixers.

Each technique is backed by real cryptographic implementations with no mock code.

================================================================================
SYSTEM REQUIREMENTS:
================================================================================

Operating System:
  - Windows 10/11 (with PowerShell 5.1+)
  - Linux (Ubuntu 20.04+ or equivalent)
  - macOS 10.14+

Python:
  - Python 3.11.9 
  - Virtual environment support (venv)

Disk Space:
  - ~2GB for project + virtual environment
  - ~500MB for media/datasets

RAM:
  - Minimum 4GB
  - 8GB+ recommended for smooth operation

Database:
  - SQLite (included, default)
  - PostgreSQL (optional, for production)

================================================================================
SETUP INSTRUCTIONS FOR NEW LAPTOP:
================================================================================

STEP 1: Clone or Copy Project
------
On Windows:
  1. Copy the entire project folder to your desired location
  2. Navigate to project root in PowerShell:
     cd 'path\to\blockchain_privacy_platform'

On Linux/macOS:
  1. Clone or copy the project
  2. Navigate to project root:
     cd /path/to/blockchain_privacy_platform

STEP 2: Create Virtual Environment
------
On Windows (PowerShell):
  p-venv\Scripts\Activate

On Linux/macOS:
  python3 -m venv p-venv
  source p-venv/bin/activate

STEP 3: Install Dependencies
------
  pip install --upgrade pip
  pip install -r requirements.txt

  (If requirements.txt doesn't exist, manually install:)
  pip install django>=3.2
  pip install django-rest-framework>=3.12
  pip install cryptography>=36.0
  pip install numpy>=1.20
  pip install pandas>=1.3
  pip install psycopg2-binary>=2.9
  pip install gunicorn>=20.1

STEP 4: Database Setup
------
  python manage.py makemigrations
  python manage.py migrate
  python manage.py migrate accounts
  python manage.py migrate admin_panel
  python manage.py migrate dashboard
  python manage.py migrate datasets
  python manage.py migrate experiments
  python manage.py migrate privacy_tools
  python manage.py migrate reports

STEP 5: Create Superuser (Admin Account)
------
  python manage.py createsuperuser
  
  Enter:
    Username: admin
    Email: admin@example.com
    Password: (choose a secure password)

STEP 6: Create Privacy Techniques (If Not Already in Database)
------
  python manage.py shell

  Inside the shell, run:
  >>> from privacy_tools.models import PrivacyTechnique
  >>> 
  >>> techniques = [
  ...     {'name': 'Ring Signature', 'type': 'ring_signature', 'security_level': 8},
  ...     {'name': 'Zero-Knowledge Proof', 'type': 'zkp', 'security_level': 10},
  ...     {'name': 'SMPC', 'type': 'smpc', 'security_level': 9},
  ...     {'name': 'Trusted Execution', 'type': 'tee', 'security_level': 9},
  ...     {'name': 'Mixer', 'type': 'mixer', 'security_level': 7},
  ... ]
  >>> 
  >>> for t in techniques:
  ...     PrivacyTechnique.objects.get_or_create(
  ...         technique_type=t['type'],
  ...         defaults={
  ...             'name': t['name'],
  ...             'security_level': t['security_level'],
  ...             'is_active': True,
  ...             'parameters': {},
  ...             'algorithm_details': ''
  ...         }
  ...     )
  >>> 
  >>> exit()

================================================================================
RUNNING THE APPLICATION:
================================================================================

OPTION 1: Development Server (Local Testing)
------
On Windows:
  p-venv\Scripts\Activate
  python manage.py runserver 127.0.0.1:8000

On Linux/macOS:
  source p-venv/bin/activate
  python manage.py runserver 127.0.0.1:8000

Then open your browser to: http://127.0.0.1:8000

Login with the superuser credentials created above.

OPTION 2: Production Server with Gunicorn
------
On Windows:
  .\p-venv\Scripts\Activate.ps1
  gunicorn privacy_platform.wsgi:application --bind 0.0.0.0:8000 --workers 4

On Linux/macOS:
  source p-venv/bin/activate
  gunicorn privacy_platform.wsgi:application --bind 0.0.0.0:8000 --workers 4

================================================================================
COMMON TASKS:
================================================================================

RUN ALL EXPERIMENTS:
  python manage.py rerun_all_report --force --out final_report.csv
  
  (Optional: Redirect output to file)
  python manage.py rerun_all_report --force --out my_results.csv

RUN SPECIFIC EXPERIMENT:
  python manage.py rerun_experiments --ids 1 --force
  python manage.py rerun_experiments --ids 1,5,10 --force

RUN N MOST RECENT EXPERIMENTS:
  python manage.py rerun_experiments --recent 10 --force

BACKFILL EXPERIMENT METRICS FROM TECHNIQUE EVALUATORS:
  python manage.py backfill_metrics

VIEW DATABASE SHELL:
  python manage.py shell

GENERATE STATIC FILES (For production):
  python manage.py collectstatic --noinput

RESET DATABASE (WARNING: Deletes all data):
  python manage.py flush

VIEW ALL EXPERIMENTS:
  http://127.0.0.1:8000/experiments/

ADMIN PANEL:
  http://127.0.0.1:8000/admin/

================================================================================
