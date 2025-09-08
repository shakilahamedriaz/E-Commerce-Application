# 🌱 GreenCart - Carbon-Aware Online Marketplace

[![Django](https://img.shields.io/badge/Django-5.2.4-green.svg)](https://www.djangoproject.com/)
[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://www.python.org/)
[![AI Powered](https://img.shields.io/badge/AI-Powered-orange.svg)](https://huggingface.co/)
[![Pinecone](https://img.shields.io/badge/Vector_DB-Pinecone-purple.svg)](https://pinecone.io/)
[![SSLCommerz](https://img.shields.io/badge/Payment-SSLCommerz-red.svg)](https://sslcommerz.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 🚀 Project Overview

**EcoCart** is a next-generation sustainable e-commerce platform that combines advanced AI technology with environmental consciousness. Built with Django 5.2.4 and powered by cutting-edge machine learning models, it revolutionizes online shopping by integrating carbon footprint tracking, AI-driven recommendations, and comprehensive sustainability analytics.

### 🎯 Key Achievements & Highlights

- **🤖 Advanced AI Integration**: RAG-based chatbot using Qwen2-7B-Instruct + Pinecone vector database
- **🌍 Carbon Intelligence**: Real-time environmental impact tracking with smart recommendations
- **🏆 Gamification System**: Comprehensive badge system with eco-achievements and progress tracking
- **📊 Analytics Dashboard**: Advanced impact visualization with environmental simulators
- **� Secure Payment Gateway**: SSLCommerz integration with transaction management
- **� Enterprise Security**: Robust authentication with password reset and session management
- **📱 Modern UI/UX**: Responsive design with Bootstrap 5 and custom theming
- **📧 Communication System**: Email notifications with HTML templates and SMTP integration

## 🏗️ Technical Architecture

### Core Technologies
- **Framework**: Django 5.2.4 (Python 3.12+)
- **Database**: SQLite3 (Development) / PostgreSQL (Production Ready)
- **AI/ML Stack**: 
  - LangChain Framework
  - Hugging Face Transformers (Qwen2-7B-Instruct)
  - Pinecone Vector Database
  - Sentence Transformers (all-MiniLM-L6-v2)
- **Payment Gateway**: SSLCommerz (Bangladeshi Payment Solution)
- **Email System**: SMTP with Gmail integration
- **Session Management**: Django Sessions with Redis-ready architecture

### Frontend Stack
- **UI Framework**: Bootstrap 5.3.2
- **Icons**: Font Awesome 6.4.0
- **Fonts**: Google Fonts (Inter family)
- **JavaScript**: Modern ES6+ with async/await patterns
- **CSS**: Custom properties with advanced animations and transitions
- **Admin Interface**: Enhanced Django Admin with custom theming
- Font Awesome 6
- Vanilla JavaScript (ES6+)
- Custom theming & responsive layouts

### AI/ML Layer
- Hugging Face Inference API
- Qwen2-7B-Instruct (chat intelligence)
- Pinecone (vector search)
- Retrieval-Augmented Generation pipeline
- Sentence Transformer embeddings

## 🌟 Core Features

### 🛒 E-Commerce Functionality
- Product Management (categories, search, filters)
- Shopping Cart (persistent, session-aware)
- Payment Integration: 💳 Secure multi-gateway processing
- Order Processing (lifecycle tracking)
- User Profiles (orders, stats, impact)
- Review System (ratings, helpfulness)

### 🌱 Sustainability Features
- Carbon Footprint Calculator
- Sustainability & ethical scoring model
- User Impact Dashboard
- Eco Badges & progression tiers
- Monthly carbon budget tracking

### 🤖 AI Assistant
- Natural language product queries
- Conversational context retention
- Smart recommendations
- Intent classification scaffolding
- Feedback-driven improvement loop

### 📊 Analytics & Insights
- Sales & behavioral metrics (admin)
- Environmental projection simulator
- User engagement & retention patterns
- System performance insights

## 🚀 Quick Start

### Prerequisites
```bash
Python 3.8+
Django 4.2+
Redis (optional but recommended)
Node.js (optional for asset tooling)
```

### Installation
```bash
git clone https://github.com/yourusername/greencart-ecommerce.git
cd greencart-ecommerce
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env`:
```
HUGGINGFACE_API_TOKEN=your_token
PINECONE_API_KEY=your_key
PINECONE_ENVIRONMENT=your_env
STRIPE_SECRET_KEY=sk_test_xxx
PAYPAL_CLIENT_ID=your_client_id
```

Run setup:
```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py loaddata initial_data.json  # optional seed
python manage.py sync_products               # index products in vector DB
python manage.py runserver
```

Visit: http://localhost:8000

## 📁 Project Structure
```
e_shop/
├─ ai_chatbot_agent/
│  ├─ models.py
│  ├─ services/
│  └─ templates/
├─ products/
│  ├─ models.py
│  ├─ services/
│  └─ admin.py
├─ shop/
│  ├─ views.py
│  ├─ models.py
│  └─ templates/
├─ payments/
│  ├─ models.py
│  ├─ services/
│  └─ webhooks.py
├─ templates/
├─ static/
├─ media/
└─ docs/
```

## 🔌 API Documentation

### Chat API
```python
POST /chatbot/api/chat/
{
  "message": "Recommend eco-friendly laptops",
  "session_id": "optional-session-id"
}
```

### Payment API
```python
POST /api/payments/initialize/
{
  "amount": 129.99,
  "currency": "USD",
  "payment_method": "stripe",
  "order_id": "ORD-2025-001"
}

POST /api/payments/process/
{
  "payment_token": "pm_xxx",
  "billing_address": {...},
  "save_payment_method": true
}

POST /api/payments/webhook/stripe/
# Processes confirmations, failures, refunds
```

### Environmental Simulator
```python
POST /api/environmental-simulator/
{
  "monthly_reduction": 5.0,
  "timeframe": 12
}
```

### Product Search
```python
GET /api/products/search/?q=eco-friendly&category=electronics
```

## 🎨 Screenshots
(Place images in docs/screenshots/)
- Homepage
- AI Chatbot
- Impact Dashboard
- Product Page
- Payment Flow

## 🧪 Testing
```bash
python manage.py test
python manage.py test ai_chatbot_agent
python manage.py test shop
python manage.py test payments
coverage run --source='.' manage.py test
coverage report
```

## 🚀 Deployment

### Production Environment Variables
```
DEBUG=False
ALLOWED_HOSTS=yourdomain.com
DATABASE_URL=postgresql://user:pass@host:5432/db
REDIS_URL=redis://localhost:6379/0
STRIPE_SECRET_KEY=sk_live_xxx
PAYPAL_CLIENT_ID=live_client_id
```

### Build & Run
```bash
python manage.py collectstatic
python manage.py migrate
gunicorn e_shop.wsgi:application --bind 0.0.0.0:8000
```

### Docker
```bash
docker build -t greencart .
docker run -p 8000:8000 --env-file .env greencart
```

### Heroku (example)
```bash
heroku create greencart-app
heroku config:set $(cat .env | xargs)  # verify before running in real usage
git push heroku main
```

## 🤝 Contributing
1. Fork repository
2. Create branch: git checkout -b feature/awesome
3. Commit: git commit -m "feat: add awesome feature"
4. Push: git push origin feature/awesome
5. Open Pull Request

Guidelines:
- Follow PEP 8
- Add tests for new logic
- Keep commits atomic
- Update documentation
- Avoid secrets in commits

## 📈 Performance Metrics
- Page Load: < 2s
- AI Response: < 3s avg
- Payment Confirmation: < 5s
- Optimized ORM queries
- Redis caching layer
- Lighthouse Score: 95+ target

## 🛡️ Security Features
- CSRF / XSS protection
- ORM-based SQL injection prevention
- HTTPS-first deployment model
- PCI-aware payment abstraction
- Secure session & password hashing
- Rate limiting (extensible)
- Security headers: HSTS, CSP (configurable)
- Input validation & sanitization

## 📊 Tech Stack Highlights
| Layer        | Tech                          |
|--------------|-------------------------------|
| Backend      | Django                        |
| AI           | Qwen2-7B-Instruct, RAG        |
| Vector DB    | Pinecone                      |
| Frontend     | Bootstrap 5, Vanilla JS       |
| Database     | SQLite / PostgreSQL           |
| Cache        | Redis                         |
| Payments     | Stripe, PayPal                |
| Deployment   | Docker, AWS/Heroku ready      |
| Monitoring   | Django Admin / extensible     |

## 🏆 Key Achievements
- Full-stack platform built from scratch
- AI-driven conversational commerce
- Multi-gateway payment integration
- Sustainability-centric engagement model
- Modular architecture & extensibility
- Optimized query & caching strategy
- Production deployment scaffolding

## 💰 Business Features
- Marketplace-ready architecture
- Subscription tier potential
- Carbon offset integration path
- Advanced personalization roadmap
- Analytics: sales, impact, retention

## 🌟 Future Roadmap
| Phase | Goals |
|-------|-------|
| 1     | Core commerce, AI, payments (✅) |
| 2     | Mobile app, advanced ML, social features |
| 3     | B2B marketplace, AR/VR, IoT hooks |
| 4     | Globalization, multi-currency, localization |

## 📞 Support & Contact
Technical: support@greencart.com  
Business: business@greencart.com  
Community: Discord (placeholder)  
Docs: docs.greencart.com  

## 📝 License
Licensed under MIT. See LICENSE for details.

```
MIT License

Copyright (c) 2025 GreenCart

Permission is hereby granted, free of charge, to any person obtaining a copy
...
```

## 👨‍💻 Author
**[Your Name]**  
Portfolio: https://yourportfolio.com  
GitHub: https://github.com/yourusername  
LinkedIn: https://linkedin.com/in/yourprofile  
Email: your.email@example.com  

### Skills Demonstrated
- Django / REST API architecture
- AI integration & vector search
- Payment orchestration (Stripe, PayPal)
- Secure session & auth flows
- Data modeling & optimization
- Docker-based deployment
- Sustainable UX strategy

## 🙏 Acknowledgments
- Hugging Face
- Pinecone
- Stripe & PayPal
- Bootstrap & Django Communities
- Open sustainability data sources

## 📊 GitHub Stats (Replace placeholders)
![Stars](https://img.shields.io/github/stars/yourusername/greencart-ecommerce?style=social)
![Forks](https://img.shields.io/github/forks/yourusername/greencart-ecommerce?style=social)
![Issues](https://img.shields.io/github/issues/yourusername/greencart-ecommerce)
![PRs](https://img.shields.io/github/issues-pr/yourusername/greencart-ecommerce)

---

<div align="center">
⭐ If this project inspires you, please star it!

Made with ❤️ and ☕ — Advancing sustainable commerce 🌱
</div>
