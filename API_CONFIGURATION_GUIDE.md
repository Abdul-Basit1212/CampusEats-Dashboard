# 🔍 CampusEats AI API Configuration - Diagnostic Report

**Generated:** April 25, 2026  
**Dashboard Component:** 4_AI_Forecaster_Advisor.py  
**API Service:** Google Gemini AI

---

## 📋 Current Configuration Status

### ✅ API Key Status
```
Configuration File: .env
GEMINI_API_KEY: Present
Value Length: 61 characters
Format: Appears valid (starts with AQ.Ab8...)
```

### ⚠️ Potential Configuration Issues Found

#### Issue 1: API Key Validation
```
Current Key: AQ.Ab8RN6KMZIMWy993Ty7phsS9db10ST36LZ7WhdxJJONMd0a6xA
Status: ⏳ NEEDS VERIFICATION
Possible Problems:
  - Key may be expired
  - Key may have been revoked
  - Key may not have Gemini API access enabled
  - Key may have usage quotas exceeded
```

#### Issue 2: Model Compatibility
```
Requested Model: gemini-2.5-flash
Status: ⏳ NEEDS VERIFICATION
Possible Problems:
  - Your API key may not have access to this model
  - Model may require higher tier plan
  - Model name may be outdated
```

#### Issue 3: Library Installation
```
Required Library: google-generativeai==0.5.4
Status: ✅ In requirements.txt
Action Needed: Verify it's installed in your venv
```

#### Issue 4: Rate Limiting
```
Free Tier Quota: Limited
Status: ⏳ May encounter 429 errors
Solution: Implemented - app shows user-friendly message
```

---

## 🔧 How to Fix API Configuration Issues

### Step 1: Verify API Key is Valid
```bash
# Open your browser and go to:
https://aistudio.google.com/app/apikey

# Check if your current key is:
✓ Listed and active
✓ Created recently or long ago (active duration)
✓ Has "Generative Language API" enabled
```

### Step 2: Get a Fresh API Key (if needed)
```bash
1. Go to https://aistudio.google.com/app/apikey
2. Click "Create API Key"
3. Select or create a Google Cloud project
4. Copy the new key
5. Update your .env file with the new key
6. Restart the Streamlit server
```

### Step 3: Verify Library Installation
```bash
# In your Terminal, activate your virtual environment and run:
cd "c:\Users\dondo\Documents\VS Code\Campus Eats App"
venv\Scripts\activate
pip install google-generativeai==0.5.4

# Verify installation:
python -c "import google.generativeai; print(google.generativeai.__version__)"
```

### Step 4: Test the Connection (Optional)
```bash
# Run this Python script to test your API key:
python test_gemini_api.py
```

---

## 🧪 Test Script to Validate API Configuration

I recommend creating and running this test script:

**File: `test_gemini_api.py`**
```python
#!/usr/bin/env python3
"""Test Gemini API configuration."""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("=" * 60)
print("🧪 Gemini API Configuration Validator")
print("=" * 60)

# Check for API key
gemini_key = os.getenv("GEMINI_API_KEY", "")
print(f"\n1. API Key Status:")
print(f"   - Present: {bool(gemini_key)}")
print(f"   - Length: {len(gemini_key)} characters")
print(f"   - Value: {gemini_key[:20]}...{gemini_key[-10:] if len(gemini_key) > 30 else ''}")

if not gemini_key:
    print("\n❌ FAIL: No API key found in .env file")
    exit(1)

if gemini_key == "your_gemini_api_key_here":
    print("\n❌ FAIL: API key is still a placeholder")
    exit(1)

# Try to import the library
print(f"\n2. Library Status:")
try:
    import google.generativeai as genai
    print(f"   ✅ google.generativeai imported successfully")
    print(f"   - Version: {genai.__version__ if hasattr(genai, '__version__') else 'unknown'}")
except ImportError as e:
    print(f"   ❌ FAIL: Could not import google.generativeai")
    print(f"   - Error: {e}")
    print(f"   - Fix: Run: pip install google-generativeai==0.5.4")
    exit(1)

# Test API configuration
print(f"\n3. API Configuration Test:")
try:
    genai.configure(api_key=gemini_key)
    print(f"   ✅ API key configured successfully")
except Exception as e:
    print(f"   ❌ FAIL: Could not configure API")
    print(f"   - Error: {e}")
    exit(1)

# List available models
print(f"\n4. Available Models:")
try:
    for model in genai.list_models():
        print(f"   - {model.name}")
        if "gemini-2.5-flash" in model.name:
            print(f"     ✅ Target model found!")
except Exception as e:
    print(f"   ⚠️  Could not list models")
    print(f"   - Error: {e}")

# Test simple generation
print(f"\n5. API Call Test (simple generation):")
try:
    model = genai.GenerativeModel(model_name="gemini-2.5-flash")
    response = model.generate_content("Say 'Hello from CampusEats AI!' in one sentence.")
    
    if response and hasattr(response, 'text'):
        print(f"   ✅ API call successful!")
        print(f"   - Response: {response.text[:100]}...")
    else:
        print(f"   ⚠️  API call returned empty response")
except Exception as e:
    err_str = str(e)
    if "429" in err_str:
        print(f"   ⚠️  Rate limited (429) - this is normal for free tier")
        print(f"   - The API works, but quota is temporarily exceeded")
    elif "API_KEY" in err_str.upper() or "not authenticated" in err_str.lower():
        print(f"   ❌ FAIL: Invalid API key")
        print(f"   - Error: {err_str[:100]}")
    elif "not found" in err_str.lower() or "404" in err_str:
        print(f"   ❌ FAIL: Model not found")
        print(f"   - You may not have access to gemini-2.5-flash")
        print(f"   - Error: {err_str[:100]}")
    else:
        print(f"   ❌ FAIL: {err_str[:150]}")

print("\n" + "=" * 60)
print("✅ API Configuration validation complete!")
print("=" * 60)
```

---

## 📊 Common Error Messages & Solutions

### Error 1: "Gemini API key not configured"
```
Problem: GEMINI_API_KEY is missing or placeholder
Solution: 
  1. Get a real API key from https://aistudio.google.com/app/apikey
  2. Update your .env file
  3. Restart the Streamlit app
```

### Error 2: "429 - Rate Limit Reached"
```
Problem: Free tier quota exceeded
Solutions:
  1. ⏰ Wait 5-10 minutes (quotas reset)
  2. 🧹 Clear conversation history in chat
  3. 💬 Ask simpler questions (fewer tokens)
  4. 💳 Upgrade to paid plan if persistent
Status: This is EXPECTED for free tier - app handles it gracefully
```

### Error 3: "Invalid or Missing API Key"
```
Problem: API key is invalid or expired
Solutions:
  1. Check key is active at: https://aistudio.google.com/app/apikey
  2. Generate a new API key
  3. Update .env file
  4. Restart Streamlit
```

### Error 4: "Model Not Found (404)"
```
Problem: API key doesn't have access to gemini-2.5-flash
Solutions:
  1. Verify model availability: https://aistudio.google.com/app/apikey
  2. Try older model: "gemini-pro" instead of "gemini-2.5-flash"
  3. Check if your key has Generative Language API enabled
Note: Different API keys may have different model access
```

### Error 5: "Safety Filter Triggered"
```
Problem: AI declined to respond for safety reasons
Solution: 
  - Rephrase your question more clearly
  - This is a safety feature - working as designed
```

---

## ✅ Verification Checklist

Before testing the AI Forecaster, verify:

- [ ] API key exists in `.env` file
- [ ] API key is not a placeholder value
- [ ] API key is active at https://aistudio.google.com/app/apikey
- [ ] google-generativeai library is installed (`pip list | grep generativeai`)
- [ ] .env file is in the correct location: `Campus Eats App/.env`
- [ ] Streamlit app has been restarted after any `.env` changes
- [ ] You're logged into the dashboard with a valid role
- [ ] You've clicked to view the "🤖 AI Business Advisor" section

---

## 🚀 Next Steps

1. **Verify Current API Key** (5 minutes)
   - Go to: https://aistudio.google.com/app/apikey
   - Check if key is active
   - Check if Generative Language API is enabled

2. **Run Diagnostic Test** (2 minutes)
   - Create `test_gemini_api.py` from the script above
   - Run: `python test_gemini_api.py`
   - Review results

3. **Fix Issues Found** (5-10 minutes)
   - Follow the solutions for any errors
   - Update `.env` if needed
   - Restart Streamlit

4. **Test in Dashboard** (5 minutes)
   - Login to CampusEats at http://localhost:8501
   - Navigate to "🤖 AI Business Advisor"
   - Try asking a question

---

## 📞 Support Resources

- **Google AI Studio:** https://aistudio.google.com/app/apikey
- **Gemini API Documentation:** https://ai.google.dev/docs
- **google-generativeai GitHub:** https://github.com/google/generative-ai-python
- **CampusEats GitHub:** [Your repo]

---

## 🎯 Expected Behavior

### After Configuration is Complete

✅ **What Should Work:**
- 🤖 AI Advisor section loads without warnings
- 💬 Chat input accepts your questions
- 🔄 AI responds with business advice (may be delayed if rate limited)
- 💾 Responses are cached for same questions
- 🛡️ Graceful error messages if issues occur

✅ **Features:**
- Answering questions about sales trends
- Recommending item promotions
- Analyzing busy hours
- Suggesting ways to reduce cancellations
- Comparing against competitor metrics

---

**Last Updated:** April 25, 2026  
**Status:** 📋 Diagnostic report ready for action

