#!/usr/bin/env python3
"""
Test Gemini API Configuration - CampusEats Dashboard
Run this script to verify your Google Gemini API is properly configured.
"""

import os
import sys

# ── PYTHON 3.14+ PROTOBUF COMPATIBILITY FIX ────────────────────────────────
# Disable UPB (C extension) for protobuf to work with Python 3.14.3
# This forces use of pure Python implementation
os.environ["PROTOBUF_PYTHON_IMPL"] = "python"

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def print_header(title):
    """Print a styled header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)

def print_section(title):
    """Print a section header."""
    print(f"\n📋 {title}")
    print("-" * 70)

def test_api_configuration():
    """Run comprehensive API configuration tests."""
    
    print_header("🧪 Gemini API Configuration Validator")
    print("\nThis script will test your Google Gemini API configuration.")
    print("It will check for API keys, library installation, and connectivity.\n")
    
    all_passed = True
    
    # ─────────────────────────────────────────────────────────────────────────
    # Test 1: Environment Variables
    # ─────────────────────────────────────────────────────────────────────────
    print_section("Test 1: Environment Variables")
    
    gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
    database_url = os.getenv("DATABASE_URL", "").strip()
    demo_mode = os.getenv("DEMO_MODE", "").strip()
    
    print(f"GEMINI_API_KEY:")
    if not gemini_key:
        print(f"  ❌ NOT FOUND - Check your .env file")
        all_passed = False
    elif gemini_key == "your_gemini_api_key_here":
        print(f"  ❌ PLACEHOLDER - Replace with real API key")
        all_passed = False
    else:
        masked_key = gemini_key[:10] + "..." + gemini_key[-8:]
        print(f"  ✅ FOUND ({len(gemini_key)} chars): {masked_key}")
    
    print(f"\nDATABASE_URL: {database_url if database_url else '❌ NOT FOUND'}")
    print(f"DEMO_MODE: {demo_mode if demo_mode else '⏳ Not set (defaults to false)'}")
    
    # ─────────────────────────────────────────────────────────────────────────
    # Test 2: Library Installation
    # ─────────────────────────────────────────────────────────────────────────
    print_section("Test 2: Library Installation")
    
    try:
        import google.generativeai as genai
        version = getattr(genai, '__version__', 'unknown')
        print(f"✅ google.generativeai imported successfully")
        print(f"   Version: {version}")
    except ImportError as e:
        print(f"❌ FAIL: Could not import google.generativeai")
        print(f"   Error: {e}")
        print(f"\n   SOLUTION: Install the package with:")
        print(f"   pip install google-generativeai==0.5.4")
        all_passed = False
        return all_passed
    
    # ─────────────────────────────────────────────────────────────────────────
    # Test 3: API Key Configuration
    # ─────────────────────────────────────────────────────────────────────────
    print_section("Test 3: API Key Configuration")
    
    if not gemini_key:
        print("⏭️  Skipping (no API key to test)")
    else:
        try:
            genai.configure(api_key=gemini_key)
            print(f"✅ API key configured successfully")
        except Exception as e:
            print(f"❌ FAIL: Could not configure API")
            print(f"   Error: {str(e)[:200]}")
            all_passed = False
    
    # ─────────────────────────────────────────────────────────────────────────
    # Test 4: List Available Models
    # ─────────────────────────────────────────────────────────────────────────
    print_section("Test 4: Available Models")
    
    if not gemini_key:
        print("⏭️  Skipping (no API key to test)")
    else:
        try:
            models = list(genai.list_models())
            print(f"✅ Successfully retrieved {len(models)} available models:\n")
            
            target_found = False
            for model in models:
                model_name = model.name
                display_name = model_name.replace("models/", "")
                
                # Highlight the target model
                if "gemini-2.5-flash" in model_name:
                    print(f"   ✅ {display_name} (TARGET MODEL)")
                    target_found = True
                elif "gemini" in model_name.lower():
                    print(f"   • {display_name}")
            
            if not target_found:
                print(f"\n   ⚠️  gemini-2.5-flash not found in available models")
                print(f"   Try: gemini-pro or check your API tier")
                all_passed = False
                
        except Exception as e:
            err_str = str(e)
            if "429" in err_str:
                print(f"⏳ Rate limited (429) - API is working but quota exceeded")
            elif "API_KEY" in err_str.upper() or "not authenticated" in err_str.lower():
                print(f"❌ FAIL: Authentication error")
                print(f"   The API key appears to be invalid")
                all_passed = False
            else:
                print(f"⚠️  Could not list models: {err_str[:150]}")
    
    # ─────────────────────────────────────────────────────────────────────────
    # Test 5: API Call Test
    # ─────────────────────────────────────────────────────────────────────────
    print_section("Test 5: Simple API Call")
    
    if not gemini_key:
        print("⏭️  Skipping (no API key to test)")
    else:
        try:
            print("Attempting to call Gemini API with a test prompt...")
            print("(This may take 5-10 seconds)\n")
            
            model = genai.GenerativeModel(model_name="gemini-2.5-flash")
            response = model.generate_content(
                "Respond with exactly this: 'CampusEats AI is working!'"
            )
            
            if response and hasattr(response, 'text'):
                print(f"✅ API call successful!")
                print(f"   Response: {response.text[:150]}")
                if "CampusEats AI is working" in response.text:
                    print(f"   ✅ Response matches expected format")
            else:
                print(f"❌ API call returned empty response")
                all_passed = False
                
        except Exception as e:
            err_str = str(e)
            print(f"Error during API call:\n")
            
            if "429" in err_str:
                print(f"⏳ Rate Limited (429)")
                print(f"   Your API key is valid, but quota is temporarily exceeded.")
                print(f"   This is NORMAL for free tier.")
                print(f"   Solution: Wait 5-10 minutes and try again.")
                print(f"\n   ℹ️  The app will work, but responses may be delayed.")
                
            elif "API_KEY" in err_str.upper() or "not authenticated" in err_str.lower():
                print(f"❌ Invalid or Missing API Key")
                print(f"   Error: {err_str[:200]}")
                print(f"   Solution:")
                print(f"   1. Get a new key: https://aistudio.google.com/app/apikey")
                print(f"   2. Update your .env file")
                print(f"   3. Restart the app")
                all_passed = False
                
            elif "not found" in err_str.lower() or "404" in err_str:
                print(f"❌ Model Not Found (404)")
                print(f"   Your API key doesn't have access to gemini-2.5-flash")
                print(f"   Error: {err_str[:200]}")
                print(f"   Solutions:")
                print(f"   1. Try using 'gemini-pro' instead")
                print(f"   2. Get a new API key with proper permissions")
                print(f"   3. Check your API tier")
                all_passed = False
                
            elif "SAFETY" in err_str.upper():
                print(f"🛡️  Safety Filter Triggered")
                print(f"   The API declined to respond for safety reasons.")
                print(f"   This is normal - the connection works.")
                print(f"   ✅ The API is accessible, just rejected this prompt.")
                
            else:
                print(f"❌ Unknown Error: {err_str[:200]}")
                all_passed = False
    
    # ─────────────────────────────────────────────────────────────────────────
    # Summary
    # ─────────────────────────────────────────────────────────────────────────
    print_header("Test Summary")
    
    if all_passed and gemini_key:
        print("✅ All tests PASSED! Your API is configured correctly.")
        print("\nYou can now:")
        print("  1. Start the Streamlit app: streamlit run Home.py")
        print("  2. Login to the dashboard")
        print("  3. Navigate to '🤖 AI Business Advisor'")
        print("  4. Ask questions about your sales data")
        return True
    elif gemini_key:
        print("⚠️  Some tests had issues, but the API may still work.")
        print("   Please review the errors above and follow the suggested solutions.")
        print("\n   Common fixes:")
        print("   • Rate limiting (429): Wait a few minutes and try again")
        print("   • Model not found: Use 'gemini-pro' instead")
        print("   • Invalid key: Get a new one from https://aistudio.google.com/app/apikey")
        return False
    else:
        print("❌ Tests FAILED - API key not configured")
        print("\n   Quick fix:")
        print("   1. Get a free API key: https://aistudio.google.com/app/apikey")
        print("   2. Add to your .env file:")
        print("      GEMINI_API_KEY=your_key_here")
        print("   3. Restart the app")
        return False

def main():
    """Main entry point."""
    try:
        success = test_api_configuration()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⏸️  Test interrupted by user.")
        sys.exit(130)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
