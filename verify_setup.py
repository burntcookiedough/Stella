import sys
import os
import subprocess

print(f"Python Executable: {sys.executable}")
print(f"Python Version: {sys.version}")

print("\n--- Dependency Check ---")
packages = ["pandas", "fastapi", "uvicorn", "streamlit", "ollama", "plotly"]
all_installed = True
for package in packages:
    try:
        __import__(package)
        print(f"✅ {package} installed")
    except ImportError:
        print(f"❌ {package} MISSING")
        all_installed = False

if not all_installed:
    print("\n⚠️  Some dependencies are missing. Run 'pip install -r requirements.txt'")

print("\n--- Ollama Connection Check ---")
try:
    import ollama
    print("Attempting to connect to Ollama (model: mistral:latest)...")
    response = ollama.chat(model='mistral:latest', messages=[
      {'role': 'user', 'content': 'Is this working? Reply with YES only.'}
    ])
    print(f"✅ Ollama Response: {response['message']['content']}")
except Exception as e:
    print(f"❌ Ollama Error: {e}")
    print("Ensure Ollama is running and you have pulled the model: 'ollama pull mistral:latest'")
