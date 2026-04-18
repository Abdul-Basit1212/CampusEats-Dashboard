import streamlit as st
import os

# Debug info
print("=" * 60)
print("DEBUG: Streamlit Page Switching Test")
print("=" * 60)
print(f"Current working directory: {os.getcwd()}")
print(f"Pages dir exists: {os.path.exists('pages')}")
print(f"Pages dir is dir: {os.path.isdir('pages')}")

pages_dir = os.path.join(os.getcwd(), 'pages')
if os.path.isdir(pages_dir):
    files = sorted([f for f in os.listdir(pages_dir) if f.endswith('.py')])
    print(f"Python files in pages/: {files}")
    for f in files:
        full_path = os.path.join(pages_dir, f)
        print(f"  - {f} (exists: {os.path.exists(full_path)})")

print("=" * 60)
