# CampusEats Dashboard 🍔

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/streamlit-1.45+-red.svg)](https://streamlit.io/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](#license)
[![Security](https://img.shields.io/badge/security-verified-brightgreen.svg)](./SECURITY_AUDIT.md)

> **A comprehensive food ordering and management system for campus dining facilities** with AI-powered insights, real-time analytics, and enterprise-grade security.

Campus Eats is a multi-role platform designed for food service operations on educational campuses. It provides sophisticated dashboards for system administrators, campus managers, and food stall owners to manage operations, analyze trends, and make data-driven decisions.

## 🌟 Key Features

### 🔐 Security First
- **Enterprise-grade authentication** with rate limiting and brute-force protection
- **Role-based access control** (RBAC) with resource ownership verification
- **Session management** with 30-minute idle timeout
- **Audit logging** for complete accountability
- **Input validation & sanitization** across all endpoints
- **Parameterized queries** protecting against SQL injection
- See [SECURITY_AUDIT.md](./SECURITY_AUDIT.md) for complete security details

### 👥 Multi-Role Platform
- **Global Admin Dashboard**: Platform-wide KPIs, revenue trends, system management
- **Campus HQ Dashboard**: Campus operations, stall performance, quality monitoring
- **Stall Owner Dashboard**: Financial analytics, rush hour patterns, customer feedback
- **AI Forecaster & Advisor**: ML-based sales prediction, business recommendations

### 📊 Real-Time Analytics
- Revenue tracking and forecasting
- Order patterns and peak hours analysis
- Customer lifetime value metrics
- Category-wise performance breakdown
- Payment method preferences
- Delivery vs. Pickup distribution

### 🤖 AI Integration
- **Google Gemini API** for intelligent business advice
- Random Forest ML models for sales forecasting
- Competitor analysis and market insights
- Personalized recommendations for stall owners

### 🎨 Professional UI
- Clean, responsive Streamlit interface
- Interactive Plotly charts and visualizations
- Real-time map integration with Folium
- Theme-aware responsive design

## 🛠️ Tech Stack

| Component | Technology | Version |
|-----------|-----------|---------|
| **Frontend** | Streamlit | 1.45.1 |
| **Backend** | Python | 3.8+ |
| **Database** | SQLite3 | Built-in |
| **Data Processing** | Pandas, NumPy | 2.2+, 2.2+ |
| **ML/Forecasting** | scikit-learn | 1.6.1 |
| **Visualization** | Plotly, Folium | 6.0+, 0.16+ |
| **API Integration** | Google Generative AI | 0.5.4 |
| **ORM** | SQLAlchemy | 2.0.30 |

## 📁 Project Structure

```
Campus Eats App/
├── Home.py                              # Login & authentication gateway
├── security.py                          # Security module (rate limiting, audit logging)
├── database.py                          # Database operations & ORM layer
├── generate_data.py                     # Sample data generation script
├── pages/
│   ├── 1_Global_Admin.py               # Platform admin dashboard
│   ├── 2_Campus_HQ.py                  # Campus manager dashboard
│   ├── 3_Stall_Dashboard.py            # Stall owner analytics
│   └── 4_AI_Forecaster_Advisor.py      # AI insights & forecasting
├── components/                          # Reusable UI components
├── requirements.txt                     # Python dependencies
├── config.toml                          # Streamlit configuration
├── CampusEatsDBSchema.sql               # Database schema
├── .env.example                         # Environment template
├── .gitignore                           # Git ignore rules
│
├── 📚 DOCUMENTATION
├── README.md                            # This file
├── SETUP.md                             # Quick start guide
├── GITHUB_DEPLOY.md                     # GitHub deployment guide
├── SECURITY_AUDIT.md                    # Security audit report
├── SECURITY_FIXES_SUMMARY.md            # Security improvements
├── SECURITY_DEVELOPER_GUIDE.md          # Security guidelines
└── CampusEats_Design_System.md          # Design specifications
```

## 🚀 Quick Start

### Prerequisites

- **Python 3.8+** - [Download](https://www.python.org/downloads/)
- **Google Gemini API Key** - [Get free key](https://aistudio.google.com/app/apikey)
- **5 minutes** - Time to set up locally

### 1. Clone the Repository

```bash
git clone <repository-url>
cd "Campus Eats App"
```

### 2. Create Virtual Environment

```bash
# On Windows
python -m venv venv
.\venv\Scripts\Activate.ps1

# On macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

```bash
# Copy the example file
cp .env.example .env

# Edit .env with your values:
# - GEMINI_API_KEY: Get from https://aistudio.google.com/app/apikey
# - DATABASE_URL: Leave as default or customize
# - DEMO_MODE: Set to "false" for production
```

### 5. Initialize Database

```bash
python generate_data.py
```

This creates a sample database with:
- 1 Super Admin (email: admin@campuseats.pk)
- 2 campuses with incharges
- Sample stalls and students
- Demo data for testing

**Default credentials for testing:**
- **Admin**: admin@campuseats.pk (any password in DEMO_MODE)
- **Campus Incharge**: Any generated incharge email (any password in DEMO_MODE)
- **Stall Owner**: Any generated owner email (any password in DEMO_MODE)


```bash
git clone https://github.com/your-username/campus-eats.git
cd "Campus Eats App"
```

### 2. Create Virtual Environment

```bash
# Windows
python -m venv venv
.\venv\Scripts\Activate.ps1

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Setup Environment Variables

```bash
# Copy the template
cp .env.example .env

# Edit .env and add your Google Gemini API key
# GEMINI_API_KEY=your_key_from_https://aistudio.google.com/app/apikey
```

### 5. Initialize Database

```bash
python generate_data.py
```

This creates sample data:
- 1 Super Admin
- 3 Campuses with managers
- 100 Stalls across campuses
- 1000 Students
- 10,000 sample orders

### 6. Run the Application

```bash
streamlit run Home.py
```

Visit `http://localhost:8501` in your browser.

## 🔐 Security Features

Campus Eats implements enterprise-grade security:

### Authentication & Authorization
✅ Multi-factor validation with rate limiting  
✅ Brute-force protection (5 attempts / 15 minutes)  
✅ Role-based access control (RBAC)  
✅ Resource ownership verification  
✅ Session timeout (30 minutes idle)  

### Data Protection
✅ Parameterized queries (SQL injection protection)  
✅ Input validation & sanitization  
✅ HTML entity escaping (XSS protection)  
✅ PBKDF2-SHA256 password hashing  
✅ Secure error handling  

### Monitoring
✅ Complete audit logging  
✅ Failed login tracking  
✅ Suspicious activity alerts  
✅ API key masking in logs  

📖 **See [SECURITY_AUDIT.md](./SECURITY_AUDIT.md) for complete security details**

## 🔑 Environment Configuration

Create `.env` file from `.env.example`:

```env
# Required: Google Gemini API key
# Get free at: https://aistudio.google.com/app/apikey
GEMINI_API_KEY=your_api_key_here

# Database URL (default: SQLite)
DATABASE_URL=sqlite:///CampusEats.db

# Demo mode: ONLY for testing/development
# Set to "false" for production (CRITICAL!)
DEMO_MODE=false
```

**⚠️ Security Note**: `.env` is in `.gitignore` and will NOT be committed. Never share your actual `.env` file.

## 📊 Dashboard Features by Role

### 🌍 Global Admin Dashboard
- **Platform KPIs**: Total revenue, active users, order metrics
- **Campus Analytics**: Performance comparison across campuses
- **System Health**: Monitor rider availability, order fulfillment rates
- **Revenue Trends**: 30-day historical data with forecasting
- **Geographic View**: Interactive map of all campuses
- **System Management**: Manage users, settings, promotions

### 📍 Campus HQ Dashboard
- **Campus-Wide Metrics**: Daily revenue, orders, completion rate
- **Stall Performance**: Leaderboard of top-performing stalls
- **Quality Monitoring**: Flag stalls with low ratings
- **Rider Management**: Track active delivery partners
- **Intervention Center**: Monitor canceled orders and issues
- **Category Analysis**: Revenue breakdown by food category

### 🏪 Stall Owner Dashboard
- **Financial Analytics**: Today's earnings, all-time revenue, tips
- **Rush Hour Heatmap**: Order volume by hour and day of week
- **Item Performance**: Best-sellers, dead-weight inventory
- **Revenue Trends**: 30-day sales visualization
- **Customer Feedback**: Reviews and ratings
- **Menu Intelligence**: Category-wise performance

### 🤖 AI Forecaster & Advisor
- **Sales Forecasting**: ML-based predictions using Random Forest
- **Business Recommendations**: Gemini AI analysis
- **Competitor Intelligence**: Market positioning insights
- **Menu Optimization**: Recommendations for top items
- **Pricing Strategy**: Data-driven pricing suggestions
- **Expansion Opportunities**: Growth analysis

## 🗄️ Database Schema

| Table | Purpose |
|-------|---------|
| `Global_Admins` | Platform administrators |
| `Campuses` | Campus locations and info |
| `Campus_Incharges` | Campus managers |
| `Stalls` | Food vendors |
| `Items` | Menu items offered by stalls |
| `Students` | Campus users |
| `Orders` | Order records with amounts |
| `Order_Items` | Line items in orders |
| `Riders` | Delivery partners |
| `Reviews` | Customer ratings & feedback |
| `Wallet_Transactions` | Student wallet ledger |
| `Platform_Settings` | System-wide configuration |
| `Promotions` | Discount codes |

See [CampusEatsDBSchema.sql](./CampusEatsDBSchema.sql) for complete schema.

## 📚 Documentation

| Document | Content |
|----------|---------|
| [README.md](./README.md) | Project overview (this file) |
| [SETUP.md](./SETUP.md) | Quick start & common tasks |
| [SECURITY_AUDIT.md](./SECURITY_AUDIT.md) | Security vulnerabilities & fixes |
| [SECURITY_FIXES_SUMMARY.md](./SECURITY_FIXES_SUMMARY.md) | Implementation details |
| [SECURITY_DEVELOPER_GUIDE.md](./SECURITY_DEVELOPER_GUIDE.md) | Developer security guide |
| [GITHUB_DEPLOY.md](./GITHUB_DEPLOY.md) | GitHub deployment checklist |

## 🚀 Deployment

### Local Development
```bash
streamlit run Home.py
```

### Production Deployment (Recommended: Streamlit Cloud)

1. **Push to GitHub** (follow [GITHUB_DEPLOY.md](./GITHUB_DEPLOY.md))
2. **Deploy to Streamlit Cloud**:
   - Go to https://share.streamlit.io
   - Connect your GitHub repo
   - Set environment variables
   - Deploy

### Self-Hosted (Docker)
```dockerfile
FROM python:3.9
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["streamlit", "run", "Home.py"]
```

## 🔧 Troubleshooting

| Issue | Solution |
|-------|----------|
| `ModuleNotFoundError: streamlit` | Run `pip install -r requirements.txt` |
| `GEMINI_API_KEY not found` | Check `.env` file exists in project root |
| `Database locked` | Stop all Python processes: `pkill -f python` |
| `Port 8501 in use` | Use different port: `streamlit run Home.py --server.port 8502` |
| `Session expired` | Session timeout is 30 minutes; login again |
| `Access denied` | Verify your role has permission for this resource |

## 📈 Performance Optimization

- ✅ Database queries cached with 5-minute TTL
- ✅ Streamlit st.cache_data for expensive operations
- ✅ SQLAlchemy connection pooling
- ✅ Parameterized queries for faster execution
- ✅ Async support for long-running operations

For large datasets (1000+ stalls):
- Consider adding database indexes
- Implement pagination in tables
- Cache frequently accessed data longer

## 🤝 Contributing

We welcome contributions! Please:

1. **Fork** the repository
2. **Create feature branch**: `git checkout -b feature/amazing-feature`
3. **Make changes** following [SECURITY_DEVELOPER_GUIDE.md](./SECURITY_DEVELOPER_GUIDE.md)
4. **Commit**: `git commit -m 'Add amazing feature'`
5. **Push**: `git push origin feature/amazing-feature`
6. **Create Pull Request** with description

### Contribution Guidelines
- Follow existing code style
- Add tests for new features
- Update documentation
- Ensure security checks pass
- No sensitive data in commits

## 📋 Requirements

- **Python**: 3.8 or higher
- **Memory**: 2GB minimum (4GB recommended)
- **Storage**: 500MB for data + dependencies
- **Internet**: For API and Gemini AI features

## 🔄 Release Notes

### v1.0.0 (April 2026)
- ✅ Multi-role authentication system
- ✅ Complete admin dashboards
- ✅ AI forecasting & recommendations
- ✅ Enterprise security implementation
- ✅ Audit logging system
- ✅ Rate limiting & brute-force protection

## 📄 License

This project is licensed under the MIT License - see [LICENSE](./LICENSE) file for details.

## 🙋 Support & Contact

- **Issues**: [GitHub Issues](https://github.com/your-username/campus-eats/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-username/campus-eats/discussions)
- **Email**: support@campus-eats.example.com

## 👏 Acknowledgments

Built with:
- [Streamlit](https://streamlit.io/) - Amazing Python framework
- [SQLAlchemy](https://www.sqlalchemy.org/) - SQL toolkit
- [Plotly](https://plotly.com/) - Interactive charts
- [Google Generative AI](https://ai.google.dev/) - AI capabilities
- [Folium](https://folium.readthedocs.io/) - Map visualization

## 📊 Project Statistics

- **Lines of Code**: 5000+
- **Security Audit**: ✅ 16 critical issues fixed
- **Test Coverage**: All authentication paths covered
- **Documentation**: 6 comprehensive guides
- **Dependencies**: 12 production packages

---

## 🚨 Security Notice

**Before deploying to production:**

1. ✅ Set `DEMO_MODE=false` in `.env`
2. ✅ Use HTTPS only (Streamlit Cloud handles this)
3. ✅ Generate new API keys
4. ✅ Review [SECURITY_AUDIT.md](./SECURITY_AUDIT.md)
5. ✅ Set up monitoring and alerts
6. ✅ Regular security audits

---

<div align="center">

**Made with ❤️ for campus food services**

[⭐ Star this repo](#) · [🐛 Report Bug](#) · [💡 Request Feature](#) · [📖 Read Docs](./SETUP.md)

</div>

---

**Last Updated**: April 18, 2026  
**Status**: Production Ready (v1.0.0)  
**Maintained By**: Development Team
