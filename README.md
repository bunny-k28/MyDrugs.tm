# 🧪 MyDrugs.tm — Educational E-Commerce Backend System

> ⚠️ **Disclaimer**: This project is for **educational and personal development** purposes only. Despite the branding, **no real or illegal drug-related transactions** are conducted or encouraged.

---

## 📦 Project Overview

**MyDrugs.tm** is a fully functional, backend-heavy e-commerce web application built with Python and Flask, tailored for learning and testing full-stack development patterns. It simulates a secure digital storefront offering user authentication, session handling, a cart system, user wallet, and basic purchase flows.

---

## 🛠️ Features

- 🔐 **User Authentication**
  - Username/password and email-based login
  - TOTP-based Two-Factor Authentication (2FA)
  - Secure session handling with Flask

- 🛒 **E-Commerce Functionality**
  - Product browsing with image support
  - Cart system with add/remove capability
  - Checkout and order processing

- 💳 **Wallet System**
  - Encrypted wallet access with hashed credentials
  - Balance management
  - Purchase logging with unique order IDs

- 👤 **User Account Management**
  - Profile edit & image uploads
  - Secure user deletion
  - Dynamic email notifications (SMTP integration)

- 📬 **Email Integration**
  - Email-based 2FA and account notifications
  - Custom HTML mail templates

- 🧪 **Tech-Ready Design**
  - Structured for modularity and testing
  - Uses `.env` secrets for environment config
  - Organized file hierarchy with proper separation of concerns

---

## 🗃️ Project Structure

```bash
bunny-k28-mydrugs.tm/
├── website.py              # Main Flask app
├── __init__.py             # Business logic & models
├── requirements.txt        # Python dependencies
├── LICENSE                 # MIT License
├── README.md               # You're here
├── Database/
│   ├── mydrugs_database.db
│   ├── product_ids.txt
│   ├── secrets.env
│   ├── user_UID_logs.txt
│   └── store/
│       ├── products.json
│       ├── product_det.json
│       ├── wallet/
│       └── cart/
└── static/
    └── images/
        ├── Item_Images/
        └── User_profileImages/
```

---

## 🧱 Tech Stack

| Layer          | Stack                                |
|----------------|----------------------------------------|
| Backend        | Python, Flask                         |
| Database       | SQLite3                               |
| Auth & Security| PyOTP, dotenv, hashed passwords       |
| Mail Server    | SMTP (Gmail)                          |
| Frontend       | HTML (Flask templates), basic CSS     |
| QR Generation  | `qrcode` Python library               |

---

## 🔧 Installation & Setup

1. **Clone the Repository**
   ```bash
   git clone https://github.com/yourusername/bunny-k28-mydrugs.tm.git
   cd bunny-k28-mydrugs.tm
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set Up Environment Variables**
   - Update `Database/secrets.env` with your SMTP and server configs:
     ```env
     PORT=8080
     DEBUG=True
     HOST="0.0.0.0"
     SMTP_SERVER=smtp.gmail.com
     SERVER_PORT=465
     HOST_SSID=your-email@gmail.com
     HOST_PSWD=your-email-password
     ```

4. **Run the App**
   ```bash
   python website.py
   ```

5. **Access in Browser**
   ```
   http://localhost:8080
   ```

---

## 👨‍💻 Author

**Arman Das**  
_This repository is maintained by Arman Das for backend architecture experimentation using Flask._

---

## 📫 Contact

Got questions or suggestions? Feel free to reach out:

- 📧 Email: [mydrugs.allhelp@gmail.com](mailto:mydrugs.allhelp@gmail.com)
- 💬 WhatsApp: [Click here to chat](https://api.whatsapp.com/send?phone=8745951248&text=MyDrugs.com)

---
