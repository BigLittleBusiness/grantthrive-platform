# GrantThrive Platform

Community-powered grant management platform for councils and NFP organizations in Australia and New Zealand.

## 🚀 Features

- **Grant Management**: Complete application lifecycle management
- **Community Forums**: Peer learning and collaboration
- **Resource Library**: Templates, guides, and best practices
- **Professional Marketplace**: Access to grant writing experts
- **Success Stories**: Showcase funded projects and outcomes

## 🏗️ Architecture

GrantThrive is built as a modern web application with:
- **Frontend**: React with TypeScript
- **Backend**: Python with FastAPI
- **Database**: PostgreSQL
- **Deployment**: Docker containers on cloud infrastructure

## 🛠️ Development Setup

### Prerequisites
- Node.js 18+
- Python 3.9+
- PostgreSQL 13+
- Docker (optional)

### Quick Start
```bash
# Clone the repository
git clone https://github.com/yourusername/grantthrive-platform.git
cd grantthrive-platform

# Setup frontend
cd frontend
npm install
npm run dev

# Setup backend (in new terminal)
cd backend
pip install -r requirements.txt
python manage.py runserver
