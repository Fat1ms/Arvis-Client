"""
PHASE 3 - TTS FACTORY - DAY 3 IMPLEMENTATION PLAN
Создание BarkTTSEngine для поддержки Bark TTS
=====================================================
"""

# 🎯 DAY 3 OBJECTIVE
Создать полнофункциональный BarkTTSEngine, наследующий от TTSEngineBase
с поддержкой Bark TTS и асинхронной загрузкой моделей.

Estimated Time: 1-2 hours


## 📋 REQUIREMENTS

### 1. BarkTTSEngine Class
Location: modules/bark_tts_engine.py
Must:
- Inherit from TTSEngineBase
- Implement all abstract methods:
  - speak(text, voice)
  - speak_streaming(chunk, voice)
  - stop()
  - health_check() -> HealthCheckResult
  - get_status() -> dict (inherited, can override)

### 2. Key Features
- Async model loading via task_manager
- Support for small model (faster) and full model
- Numpy/torch audio generation
- Streaming with buffering (like Silero)
- Voice selection (support bark voices)
- Health checks with model diagnostics
- Graceful degradation if bark unavailable

### 3. Configuration Support
```json
{
  "tts": {
    "bark": {
      "use_small_model": true,
      "model_size": "small",  // "small" or "full"
      "device": "cpu",        // "cpu" or "cuda"
      "np_load_scale": 1.0,   // memory optimization
      "use_cache": true
    }
  }
}
```

### 4. Test Coverage
Create: tests/unit/test_bark_tts_engine.py
Target: 15+ test cases
Classes:
- TestBarkEngineBasics (5 tests)
- TestBarkEngineInitialization (3 tests)
- TestBarkEngineStreaming (3 tests)
- TestBarkEngineVoiceSelection (2 tests)
- TestBarkEngineHealthCheck (2 tests)


## 📝 IMPLEMENTATION OUTLINE

### Step 1: Create Base Structure
```python
# modules/bark_tts_engine.py

from pathlib import Path
import sys
from typing import Optional, List, Dict
import asyncio

from config.config import Config
from modules.tts_base import TTSEngineBase, TTSStatus, HealthCheckResult
from utils.logger import ModuleLogger
from utils.async_manager import task_manager

class BarkTTSEngine(TTSEngineBase):
    def __init__(self, config: Config, logger: Optional[ModuleLogger] = None):
        self.config = config
        self.logger = logger or ModuleLogger("BarkTTSEngine")
        
        # Configuration
        self.use_small_model = config.get("tts.bark.use_small_model", True)
        self.device = config.get("tts.bark.device", "cpu")
        self.np_load_scale = config.get("tts.bark.np_load_scale", 1.0)
        
        # State
        self.model = None
        self.is_ready_flag = False
        self.is_speaking = False
        self.text_buffer = ""
        self.min_buffer_size = 20
        
        # Initialize
        self._init_bark()
```

### Step 2: Implement Abstract Methods
```python
def speak(self, text: str, voice: Optional[str] = None):
    """Speak via Bark"""
    task_manager.run_async(
        f"bark_speak_{id(self)}",
        self._speak_async,
        args=(text, voice)
    )

def speak_streaming(self, text_chunk: str, voice: Optional[str] = None):
    """Buffered streaming speak"""
    self.text_buffer += text_chunk
    if len(self.text_buffer) >= self.min_buffer_size:
        self.speak(self.text_buffer, voice)
        self.text_buffer = ""

def stop(self):
    """Stop playback"""
    # Implementation depends on playback mechanism
    pass

def health_check(self) -> HealthCheckResult:
    """Check engine health"""
    if not self.is_ready_flag:
        return HealthCheckResult(
            healthy=False,
            message="Bark model not loaded",
            details={"model_loaded": self.model is not None}
        )
    
    # Try quick synthesis
    try:
        audio = self._synthesize_test("тест")
        if audio is None:
            return HealthCheckResult(healthy=False, message="Audio generation failed")
    except Exception as e:
        return HealthCheckResult(healthy=False, message=str(e))
    
    return HealthCheckResult(
        healthy=True,
        message="Bark TTS healthy",
        details={"model": self.use_small_model and "small" or "full"}
    )
```

### Step 3: Implement Initialization
```python
def _init_bark(self):
    """Load Bark model asynchronously"""
    self.logger.info("Initializing Bark TTS...")
    
    try:
        import bark
        self.logger.debug("Bark library available")
    except ImportError:
        self.logger.error("Bark not installed: pip install bark-ml")
        self.is_ready_flag = False
        return
    
    # Load model async
    task_manager.run_async(
        "bark_model_load",
        self._load_model_async,
        on_complete=self._on_model_loaded
    )

async def _load_model_async(self):
    """Async model loading"""
    try:
        import bark
        from bark import SAMPLE_RATE, ALLOWED_PROMPTS
        
        # Select model size
        if self.use_small_model:
            # Load small model
            pass
        else:
            # Load full model
            pass
        
        self.logger.info("✓ Bark model loaded")
        return True
    except Exception as e:
        self.logger.error(f"Failed to load Bark: {e}")
        return False

def _on_model_loaded(self, task_id, result):
    """Callback after model loaded"""
    if result:
        self.is_ready_flag = True
        self.logger.info("Bark ready for synthesis")
    else:
        self.is_ready_flag = False
```

### Step 4: Voice Management
```python
def get_available_voices(self) -> List[str]:
    """Get available Bark voices"""
    return [
        "v2/en_speaker_0",
        "v2/en_speaker_1",
        "v2/en_speaker_2",
        "v2/ru_speaker_0",
        # etc
    ]

def set_voice(self, voice: str) -> bool:
    """Set active voice"""
    if voice in self.get_available_voices():
        self.voice = voice
        self.config.set("tts.bark.voice", voice)
        return True
    return False
```

### Step 5: Synthesis Methods
```python
async def _speak_async(self, text: str, voice: Optional[str] = None):
    """Async synthesis and playback"""
    try:
        audio = await self._synthesize_async(text, voice)
        if audio is not None:
            self._play_audio(audio)
    except Exception as e:
        self.logger.error(f"Bark synthesis error: {e}")

async def _synthesize_async(self, text: str, voice: Optional[str] = None) -> Optional[np.ndarray]:
    """Synthesize audio from text"""
    if not self.is_ready_flag or self.model is None:
        return None
    
    try:
        import bark
        voice = voice or self.voice or "v2/en_speaker_0"
        
        audio_array = bark.generate_audio(
            text,
            history_prompt=voice,
            text_temp=0.7,
            waveform_temp=0.7
        )
        
        return audio_array
    except Exception as e:
        self.logger.error(f"Synthesis failed: {e}")
        return None
```


## 🧪 TEST STRUCTURE

```python
# tests/unit/test_bark_tts_engine.py

class TestBarkEngineBasics:
    def test_bark_inherits_from_base(self):
    def test_bark_has_required_methods(self):
    def test_bark_import_error_handling(self):
    def test_bark_model_loading(self):
    def test_bark_configuration_loading(self):

class TestBarkEngineInitialization:
    def test_bark_init_with_small_model(self):
    def test_bark_init_with_full_model(self):
    def test_bark_device_selection(self):

class TestBarkEngineStreaming:
    def test_bark_speak_streaming_buffering(self):
    def test_bark_speak_streaming_triggers_on_boundary(self):
    def test_bark_flush_buffer(self):

class TestBarkEngineVoiceSelection:
    def test_bark_get_available_voices(self):
    def test_bark_set_voice(self):

class TestBarkEngineHealthCheck:
    def test_bark_health_check_not_ready(self):
    def test_bark_health_check_healthy(self):
```


## ✅ ACCEPTANCE CRITERIA

- [ ] BarkTTSEngine created and inherits from TTSEngineBase
- [ ] All abstract methods implemented
- [ ] Async model loading via task_manager
- [ ] Streaming with adaptive buffering
- [ ] Voice selection support
- [ ] health_check() returns HealthCheckResult
- [ ] Configuration integration
- [ ] 15+ tests all passing
- [ ] Error handling for missing bark library
- [ ] Auto-registration in TTSFactory (should be automatic)
- [ ] Clean imports and no circular dependencies
- [ ] Full docstrings


## 📚 REFERENCE IMPLEMENTATIONS

See modules/silero_tts_engine.py for patterns:
- Async initialization pattern
- health_check() structure
- speak_streaming() buffer logic
- Error handling approach
- Voice mapping normalization


## 🔗 DEPENDENCIES

```
bark-ml          # Main library
numpy            # Audio array operations
scipy            # Audio processing
torch            # If using pytorch backend
librosa          # (optional) audio analysis
```

Install: `pip install bark-ml`


## 🚀 READY FOR DAY 3?

✅ SileroTTSEngine reference exists
✅ TTSEngineBase interface defined
✅ TTSFactory registration tested
✅ Test patterns established
✅ Async/await patterns proven
✅ Configuration system ready
✅ Documentation complete

**Let's build BarkTTSEngine! 💪**

---
**Estimated Duration**: 1-2 hours
**Complexity**: Medium (model loading + async)
**Prior Art**: SileroTTSEngine (see modules/silero_tts_engine.py)
**Success Metric**: 15+ tests passing + factory registration working
