# Blockchain Privacy Platform

A Django-based platform for evaluating and experimenting with blockchain privacy techniques including Ring Signatures, Zero-Knowledge Proofs (ZKPs), Secure Multi-Party Computation (SMPC), Trusted Execution Environments (TEEs), and Cryptocurrency Mixers.

## Features

- **Privacy Techniques** — Configure and run experiments across 5 privacy-preserving techniques
- **Real-Time Experiment Runner** — Computes realistic privacy scores based on cryptographic properties (anonymity set size, entropy, information leakage, computational overhead)
- **Audit Trail** — All operations are logged with full auditability
- **Admin Panel** — Django admin interface for managing techniques, experiments, and users
- **Dashboard & Reports** — Visualize experiment results with charts and exportable reports
- **Accounts & Roles** — Researcher and administrator role-based access
- **Notifications** — In-app notifications for experiment completion and system events

## Tech Stack

- **Backend:** Django 5.0, Python 3.x
- **Database:** MySQL
- **Cryptography:** pycryptodome, cryptography, py-ecc
- **Data Analysis:** pandas, numpy, scikit-learn, scipy
- **Visualization:** matplotlib, seaborn

## Apps

| App | Description |
|---|---|
| `privacy_tools` | Core privacy technique definitions and execution |
| `experiments` | Experiment management, configuration, and result tracking |
| `accounts` | User authentication, roles (researcher/admin) |
| `dashboard` | Visual analytics dashboard |
| `audit` | Immutable audit logging for all operations |
| `reports` | Report generation and export |
| `notifications` | In-app notification system |
| `admin_panel` | Extended admin functionality |
| `share` | Sharing and collaboration features |
| `export` | Data export utilities |
| `datasets` | Dataset management for experiments |

## Installation

1. **Clone the repo**
   ```bash
   git clone <repo-url>
   cd blockchain_privacy_platform
   ```

2. **Set up virtual environment**
   ```bash
   python -m venv venv
   venv\Scripts\activate  # Windows
   source venv/bin/activate  # Linux/Mac
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   # Edit .env with your database credentials and Django secret key
   ```

5. **Run migrations**
   ```bash
   python manage.py migrate
   ```

6. **Start the server**
   ```bash
   python manage.py runserver
   ```

## Supported Privacy Techniques

- **Ring Signatures** — Anonymity through signature obfuscation within a group of possible signers
- **Zero-Knowledge Proofs (ZKP)** — Prove knowledge of a secret without revealing the secret itself
- **Secure Multi-Party Computation (SMPC)** — Joint computation across parties without revealing private inputs
- **Trusted Execution Environments (TEE)** — Hardware-level isolation for sensitive computations
- **Cryptocurrency Mixers** — Obfuscation of transaction trails through coin mixing
