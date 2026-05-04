# 🔧 CampusEats AI API - Complete Fix Guide

**Status:** 🔴 **API Key Invalid/Unauthorized**  
**Date:** April 25, 2026

---

## ✅ What's Fixed

✅ **Python Compatibility Issue** - RESOLVED
- Switched to Python 3.11 (from 3.14.3)
- All libraries now install and import correctly
- Protobuf, gRPC, and google-generativeai working

✅ **Library Installation** - RESOLVED
- google-generativeai==0.5.4 ✅
- protobuf==4.25.3 ✅
- grpcio==1.62.1 ✅
- cffi==1.17.1 ✅

---

## ❌ Current Issue: Invalid API Key

**Error:** `401 Request had invalid authentication credentials.`

**What this means:**
- The API key `AQ.Ab8RN6KMZIMWy993Ty7phsS9db10ST36LZ7WhdxJJONMd0a6xA` is invalid
- It's either expired, revoked, or never authorized for Gemini API
- You need a **new, valid API key**

---

## 🚀 How to Get a Valid API Key

### Step 1: Delete the Old Key

1. Go to: **https://aistudio.google.com/app/apikey**
2. You should see your old key listed
3. Click the **trash/delete icon** next to it
4. Confirm deletion

### Step 2: Create a New Key

1. Still at: **https://aistudio.google.com/app/apikey**
2. Click **"Create API Key"** button
3. Choose:
   - **Create new API key in a new project** (recommended for first time)
   - OR select an existing Google Cloud project
4. Click **"Create"**
5. Your new key will be displayed (looks like: `AIzaSy...` or `AQ.Ab8...`)
6. **Copy** this key immediately

### Step 3: Update Your .env File

1. Open: `c:\Users\dondo\Documents\VS Code\Campus Eats App\.env`
2. Find this line:
   ```
   GEMINI_API_KEY=AQ.Ab8RN6KMZIMWy993Ty7phsS9db10ST36LZ7WhdxJJONMd0a6xA
   ```
3. Replace with:
   ```
   GEMINI_API_KEY=YOUR_NEW_KEY_HERE
   ```
   (Paste your new key)
4. **Save** the file

### Step 4: Restart the Dashboard

1. **Stop** the Streamlit server (if running):
   - Press `Ctrl+C` in the terminal

2. **Start** it again:
   ```bash
   cd "c:\Users\dondo\Documents\VS Code\Campus Eats App"
   venv\Scripts\activate
   streamlit run Home.py
   ```

3. **Test** the AI Advisor:
   - Login to the dashboard: http://localhost:8501
   - Navigate to "🤖 AI Business Advisor"
   - Try asking a question

---

## ⚙️ Environment Setup Summary

Your system is now configured as:

```
Component                   Status    Details
─────────────────────────────────────────────────────────
Python Version              ✅        3.11 (compatible)
Virtual Environment         ✅        Active & working
google-generativeai         ✅        0.5.4 installed
protobuf                    ✅        4.25.3 installed
grpcio                      ✅        1.62.1 installed
cffi                        ✅        1.17.1 installed
Database                    ✅        CampusEats.db ready
API Key                     ❌        NEEDS REPLACEMENT
```

---

## 🧪 Verify Fix Works

After updating your API key and restarting:

```bash
# Run the test to verify:
cd "c:\Users\dondo\Documents\VS Code\Campus Eats App"
venv\Scripts\activate
python test_gemini_api.py
```

You should see:
```
✅ All tests PASSED! Your API is configured correctly.
```

---

## 📞 Troubleshooting

### Still Getting "401 Unauthorized"?

**Possible causes:**

1. **Old key still in .env** 
   - Delete old key from Google AI Studio
   - Wait 2-3 minutes
   - Try again

2. **Key not copied correctly**
   - Go back to https://aistudio.google.com/app/apikey
   - Copy the full key again
   - Paste carefully into .env

3. **Wrong API key format**
   - Keys starting with `AIzaSy...` are also valid
   - Keys starting with `AQ.Ab8...` are also valid
   - Both formats work

4. **Need to enable the API**
   - Keys created in older projects might need API enablement
   - Create a new key (easiest solution)

### Getting "Rate Limited (429)"?

This is **NORMAL** and **EXPECTED**:
- Free tier has daily usage limits
- Error handling is built in to the app
- User sees helpful message: "Wait 5-10 minutes"
- App will continue working after quota resets

**This is NOT an error you need to fix** - it's a feature!

### Getting "Model Not Found (404)"?

- Your key doesn't have access to `gemini-2.5-flash`
- Solution: Create a new API key (fresh keys have all models)
- Or try using `gemini-pro` instead (older model, always available)

---

## 🎯 Current Production Status

| Component | Status | Action |
|-----------|--------|--------|
| Dashboard | ✅ Running | http://localhost:8501 |
| Database | ✅ Ready | CampusEats.db migrated v4.0 |
| Forecasting | ✅ Ready | ML models trained |
| AI Advisor | ⏳ Needs Key | Get new API key |
| Global Admin | ✅ Working | All features operational |
| Campus HQ | ✅ Working | All features operational |

---

## 📋 Quick Checklist

- [ ] Got new API key from https://aistudio.google.com/app/apikey
- [ ] Deleted old invalid key
- [ ] Updated .env with new key
- [ ] Restarted Streamlit server
- [ ] Tested AI Advisor - asking a question
- [ ] Verified response received

---

## 🚀 Next Steps

1. **Get API Key** (5 minutes) → https://aistudio.google.com/app/apikey
2. **Update .env** (2 minutes) → Copy new key to your config
3. **Restart Server** (1 minute) → Stop and restart Streamlit
4. **Test AI Advisor** (2 minutes) → Ask a test question
5. **Enjoy!** → Full dashboard with AI capabilities working

---

## 📞 Support Resources

- **Google AI Studio:** https://aistudio.google.com
- **API Documentation:** https://ai.google.dev/docs
- **Get Free Key:** https://aistudio.google.com/app/apikey (no credit card needed)

---

## 🎉 Expected Behavior (After Fix)

### What Will Work:
✅ "🤖 AI Business Advisor" section loads  
✅ Chat input accepts questions  
✅ AI responds with business advice  
✅ Responses are cached  
✅ Rate limiting handled gracefully  

### Example Questions AI Can Answer:
- "Why did my revenue drop this week?"
- "Which items should I promote?"
- "What is my busiest day?"
- "How can I reduce cancellation rate?"
- "What's my competitor analysis?"

---

**Updated:** April 25, 2026  
**Python Version:** 3.11 (stable, compatible)  
**API Status:** Ready for new key configuration

