"""
Быстрая диагностика проблем запуска Arvis
"""

import sys
import time

print("=" * 60)
print("🔍 Arvis Startup Diagnostics")
print("=" * 60)

# 1. Python version
print(f"\n✅ Python version: {sys.version}")

# 2. PyQt5 import
print("\n⏳ Testing PyQt5 import...")
try:
    from PyQt5.QtWidgets import QApplication

    print("✅ PyQt5 OK")
except Exception as e:
    print(f"❌ PyQt5 FAILED: {e}")
    sys.exit(1)

# 3. Vosk import
print("\n⏳ Testing Vosk import...")
try:
    import vosk

    print(f"✅ Vosk OK (version: {vosk.__version__ if hasattr(vosk, '__version__') else 'unknown'})")
except Exception as e:
    print(f"❌ Vosk FAILED: {e}")

# 4. PyTorch import (может быть долгим)
print("\n⏳ Testing PyTorch import (may take 10-30 seconds)...")
torch_start = time.time()
try:
    import torch

    torch_time = time.time() - torch_start
    print(f"✅ PyTorch OK (loaded in {torch_time:.2f}s, version: {torch.__version__})")
except Exception as e:
    torch_time = time.time() - torch_start
    print(f"❌ PyTorch FAILED after {torch_time:.2f}s: {e}")

# 5. Config loading
print("\n⏳ Testing config loading...")
try:
    from config.config import Config

    config = Config()
    print(f"✅ Config OK")
    print(f"   - STT model: {config.get('stt.model_path')}")
    print(f"   - TTS enabled: {config.get('tts.enabled')}")
except Exception as e:
    print(f"❌ Config FAILED: {e}")

# 6. Check model files
print("\n⏳ Checking model files...")
import os

models_dir = "models"
if os.path.exists(models_dir):
    print(f"✅ Models directory exists")
    for item in os.listdir(models_dir):
        if os.path.isdir(os.path.join(models_dir, item)):
            print(f"   📁 {item}")
else:
    print(f"❌ Models directory NOT FOUND")

print("\n" + "=" * 60)
print("✅ Diagnostics complete!")
print("=" * 60)
