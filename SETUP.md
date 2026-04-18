# Quick Setup & Common Tasks

## ⚡ Quick Start (5 minutes)

```bash
# 1. Activate virtual environment
.\venv\Scripts\Activate.ps1          # Windows
source venv/bin/activate             # macOS/Linux

# 2. Install dependencies (if needed)
pip install -r requirements.txt

# 3. Create .env file
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY

# 4. Run the app
streamlit run Home.py
```

## 🗄️ Database Operations

### Initialize with Sample Data
```bash
python generate_data.py
```

### Reset Database
```bash
rm CampusEats.db
python generate_data.py
```

### Access Database Directly
```bash
sqlite3 CampusEats.db
```

## 🐛 Debugging

### Enable Debug Output
```bash
streamlit run Home.py --logger.level=debug
```

### Stop All Running Instances
```bash
# Windows
Stop-Process -Name streamlit -Force
Get-Process python | Stop-Process -Force

# macOS/Linux
pkill -f streamlit
pkill -f python
```

### View Recent Logs
```bash
tail streamlit_errors.log  # macOS/Linux
Get-Content streamlit_errors.log -Tail 50  # Windows
```

## 📝 Environment Variables Reference

### Development Mode
```env
GEMINI_API_KEY=your_dev_key
DATABASE_URL=sqlite:///CampusEats.db
DEMO_MODE=true
```

### Production Mode
```env
GEMINI_API_KEY=your_prod_key
DATABASE_URL=sqlite:///CampusEats.db
DEMO_MODE=false
```

## 🔐 Security Checklist Before Production

- [ ] `.env` file is NOT committed (check `.gitignore`)
- [ ] `DEMO_MODE` is set to `false`
- [ ] All API keys are regenerated for production
- [ ] Database backups are in place
- [ ] HTTPS is enabled
- [ ] No debug logs in production
- [ ] All test data is removed

## 📦 Dependency Management

### Add New Package
```bash
pip install package_name
pip freeze > requirements.txt
git add requirements.txt
```

### Update All Packages
```bash
pip install --upgrade pip
pip install -r requirements.txt --upgrade
pip freeze > requirements.txt
```

## 🔄 Git Workflow

### Before First Commit
```bash
# Verify .gitignore is working
git status
# Should NOT show: .env, venv/, __pycache__/, *.db, *.log
```

### Prepare for GitHub
```bash
git add .
git commit -m "Initial commit: Campus Eats App"
git remote add origin https://github.com/username/campus-eats.git
git push -u origin main
```

## ⚠️ Files NOT to Commit

These are automatically ignored by `.gitignore`:

- `.env` - Contains API keys and secrets
- `*.db` - Database files with sensitive data
- `venv/` - Virtual environment (can be reinstalled)
- `__pycache__/` - Python cache files
- `*.log` - Log files
- `.vscode/` - IDE settings

## 🚀 Deployment

### Before Deployment
1. Set all environment variables in production environment
2. Set `DEMO_MODE=false`
3. Ensure database is properly backed up
4. Run all tests
5. Review security settings

### Heroku Deployment Example
```bash
# Create Procfile
echo "web: streamlit run Home.py --server.port=\$PORT" > Procfile

# Deploy
git push heroku main
```

## 📊 Performance Optimization

- Enable browser cache for static assets
- Use CDN for large files
- Implement database indexing for frequently queried fields
- Consider caching with Redis for production

## 🆘 Common Issues & Solutions

| Issue | Solution |
|-------|----------|
| "ModuleNotFoundError" | Run `pip install -r requirements.txt` |
| "GEMINI_API_KEY not found" | Check `.env` file exists and is in project root |
| "Port 8501 already in use" | Run on different port: `streamlit run Home.py --server.port 8502` |
| "Database locked" | Kill all Python processes: `pkill -f python` |
| "Import error in pages" | Ensure you're in project root directory when running |

---

For detailed setup instructions, see [README.md](README.md)
