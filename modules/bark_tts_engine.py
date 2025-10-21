"""
Bark TTS Engine - refactored to inherit from TTSEngineBase
Bark TTS Движок - рефакторирован для наследования от TTSEngineBase
"""

import sys
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import numpy as np

# Setup path for imports
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from config.config import Config
from modules.tts_base import TTSEngineBase, TTSStatus, HealthCheckResult
from utils.logger import ModuleLogger


class BarkTTSEngine(TTSEngineBase):
    """Bark TTS engine for speech synthesis
    
    Поддерживает синтез речи через Bark с опциональной загрузкой модели.
    """

    def __init__(self, config: Config, logger: Optional[ModuleLogger] = None):
        """Initialize Bark TTS engine
        
        Args:
            config: Application configuration
            logger: Optional logger instance
        """
        self.config = config
        self.logger = logger or ModuleLogger("BarkTTSEngine")
        
        # Configuration
        self.use_small_model = config.get("tts.bark.use_small_model", True)
        self.model_size = config.get("tts.bark.model_size", "small" if self.use_small_model else "full")
        self.device = config.get("tts.bark.device", "cpu")
        self.np_load_scale = config.get("tts.bark.np_load_scale", 1.0)
        self.use_cache = config.get("tts.bark.use_cache", True)
        
        # State
        self.model = None
        self.is_ready_flag = False
        self.is_speaking = False
        self.current_audio = None
        self.text_buffer = ""
        self.min_buffer_size = 20
        self.word_boundary_chars = [" ", ".", ",", "!", "?", ";", ":", "\n", "\t"]
        
        # Voice settings
        self.voice = config.get("tts.bark.voice", "v2/en_speaker_0")
        
        # Initialize
        self._init_bark()

    def _init_bark(self):
        """Initialize Bark TTS model
        
        Инициализировать модель Bark.
        Загрузка модели выполняется асинхронно через task_manager.
        """
        try:
            self.logger.info("Initializing Bark TTS...")
            
            # Check if bark is available
            try:
                import bark
                self.logger.debug("Bark library available")
                self._bark = bark
            except ImportError:
                self.logger.warning("Bark not installed. Install with: pip install bark-ml")
                self.is_ready_flag = False
                return
            
            # Start async model loading
            from utils.async_manager import task_manager
            task_manager.run_async(
                "bark_model_load",
                self._load_model_async,
                on_complete=self._on_model_loaded,
                on_error=self._on_model_load_error
            )
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Bark: {e}")
            self.is_ready_flag = False

    async def _load_model_async(self):
        """Load Bark model asynchronously
        
        Загружать модель Bark в отдельном потоке.
        """
        try:
            self.logger.info(f"Loading Bark model ({self.model_size})...")
            
            # Set up environment for memory optimization
            if self.np_load_scale < 1.0:
                os.environ['BARK_SAMPLE_CACHE_DIR'] = str(Path(self.config.get("paths.cache", "temp")) / "bark_cache")
            
            # Try to load the model
            try:
                import bark
                
                # Bark models are loaded on first use, so we just check availability
                self.logger.info(f"✓ Bark model ready ({self.model_size})")
                return True
                
            except Exception as e:
                self.logger.error(f"Failed to load Bark model: {e}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error in model loading: {e}")
            return False

    def _on_model_loaded(self, task_id, result):
        """Callback when model is loaded
        
        Вызывается после загрузки модели.
        """
        if result:
            self.is_ready_flag = True
            self.logger.info("✓ Bark TTS ready for synthesis")
        else:
            self.is_ready_flag = False
            self.logger.error("Bark TTS model failed to load")

    def _on_model_load_error(self, task_id, error):
        """Callback on model load error
        
        Вызывается при ошибке загрузки.
        """
        self.logger.error(f"Bark model loading error: {error}")
        self.is_ready_flag = False

    def speak(self, text: str, voice: Optional[str] = None):
        """Convert text to speech and play it asynchronously
        
        Args:
            text: Text to synthesize
            voice: Optional voice name
        """
        if not text or not text.strip():
            return
        
        if self.is_speaking:
            self.logger.warning("Already speaking, stopping current playback")
            self.stop()
        
        from utils.async_manager import task_manager
        
        def tts_task():
            try:
                self.logger.info(f"Starting Bark TTS for: {text[:50]}...")
                
                if not self.is_ready_flag:
                    self.logger.warning("Bark not ready, trying anyway...")
                
                # Synthesize
                audio = self._synthesize(text, voice)
                if audio is not None:
                    self._play_audio_async(audio)
                    return True
                else:
                    self.logger.error("Failed to generate audio")
                    return False
                    
            except Exception as e:
                self.logger.error(f"Error in Bark TTS: {e}")
                return False
        
        # Run async
        import time
        unique_task_name = f"bark_speak_{int(time.time() * 1000)}"
        task_manager.run_async(unique_task_name, tts_task)

    def speak_streaming(self, text_chunk: str, voice: Optional[str] = None):
        """Speak text chunk for streaming mode with buffering
        
        Args:
            text_chunk: Text chunk to add to buffer
            voice: Optional voice name
        """
        if not text_chunk:
            return
        
        # Add chunk to buffer
        self.text_buffer += text_chunk
        
        # Check if we have enough text
        if len(self.text_buffer) >= self.min_buffer_size:
            # Find the last word boundary
            speak_text = ""
            remaining_buffer = self.text_buffer
            
            # Look for the last word boundary to avoid cutting words
            for i in range(len(self.text_buffer) - 1, -1, -1):
                if self.text_buffer[i] in self.word_boundary_chars:
                    speak_text = self.text_buffer[: i + 1].strip()
                    remaining_buffer = self.text_buffer[i + 1 :]
                    break
            
            # If no boundary found but buffer is too large, speak anyway
            if not speak_text and len(self.text_buffer) > self.min_buffer_size * 2:
                speak_text = self.text_buffer
                remaining_buffer = ""
            
            # Speak the text if we have something to say
            if speak_text:
                self.speak(speak_text, voice)
                self.text_buffer = remaining_buffer

    def stop(self):
        """Stop current TTS playback"""
        try:
            if self.is_speaking:
                self.is_speaking = False
                self.current_audio = None
                self.logger.info("Bark TTS playback stopped")
        except Exception as e:
            self.logger.error(f"Error stopping Bark TTS: {e}")

    def flush_buffer(self, voice: Optional[str] = None):
        """Flush remaining text in buffer
        
        Args:
            voice: Optional voice name
        """
        if self.text_buffer.strip():
            self.speak(self.text_buffer.strip(), voice)
            self.text_buffer = ""

    def health_check(self) -> HealthCheckResult:
        """Check TTS engine health
        
        Returns:
            HealthCheckResult with health status
        """
        try:
            # Check if bark is available
            try:
                import bark
            except ImportError:
                return HealthCheckResult(
                    healthy=False,
                    message="Bark library not installed",
                    details={"error": "pip install bark-ml"}
                )
            
            # Check if model is loaded
            if not self.is_ready_flag:
                return HealthCheckResult(
                    healthy=False,
                    message="Bark model not loaded yet",
                    details={"model_loaded": False}
                )
            
            # Try a quick synthesis
            try:
                audio = self._synthesize("тест", self.voice)
                if audio is None:
                    return HealthCheckResult(
                        healthy=False,
                        message="Audio generation failed",
                        details={"test_audio": None}
                    )
            except Exception as e:
                return HealthCheckResult(
                    healthy=False,
                    message=f"Synthesis test failed: {str(e)[:100]}",
                    details={"error": str(e)[:100]}
                )
            
            return HealthCheckResult(
                healthy=True,
                message="Bark TTS healthy",
                details={
                    "model_size": self.model_size,
                    "device": self.device,
                    "voice": self.voice
                }
            )
            
        except Exception as e:
            return HealthCheckResult(
                healthy=False,
                message=f"Health check error: {str(e)[:100]}",
                details={"error": str(e)[:100]}
            )

    def _synthesize(self, text: str, voice: Optional[str] = None) -> Optional[np.ndarray]:
        """Synthesize audio from text
        
        Args:
            text: Text to synthesize
            voice: Voice to use
            
        Returns:
            Audio array or None
        """
        if not self.is_ready_flag:
            return None
        
        try:
            import bark
            
            voice = voice or self.voice
            self.logger.debug(f"Synthesizing: {text[:30]}... with voice: {voice}")
            
            # Generate audio
            audio_array = bark.generate_audio(
                text,
                history_prompt=voice,
                text_temp=0.7,
                waveform_temp=0.7
            )
            
            if audio_array is not None:
                # Ensure it's a numpy array
                if not isinstance(audio_array, np.ndarray):
                    audio_array = np.asarray(audio_array, dtype=np.float32)
                
                self.logger.debug(f"Generated audio: {audio_array.shape}")
                return audio_array
            else:
                self.logger.warning("Synthesis returned None")
                return None
                
        except Exception as e:
            self.logger.error(f"Synthesis error: {e}")
            return None

    def _play_audio_async(self, audio_data: np.ndarray):
        """Play audio asynchronously
        
        Args:
            audio_data: Audio data to play
        """
        import threading
        
        def play():
            try:
                self.is_speaking = True
                self.current_audio = audio_data
                
                try:
                    import sounddevice as sd
                    
                    # Bark typically generates at 24kHz
                    sample_rate = self.config.get("tts.sample_rate", 24000)
                    
                    sd.play(audio_data, samplerate=sample_rate)
                    sd.wait()  # Wait in separate thread
                    
                except Exception as pe:
                    self.logger.error(f"Audio playback failed: {pe}")
                
                self.is_speaking = False
                self.current_audio = None
                
            except Exception as e:
                self.logger.error(f"Error playing audio: {e}")
                self.is_speaking = False
        
        thread = threading.Thread(target=play, daemon=True)
        thread.start()

    def is_ready(self) -> bool:
        """Check if TTS engine is ready"""
        return self.is_ready_flag

    def get_available_voices(self) -> List[str]:
        """Get list of available voices
        
        Returns:
            List of available voice names
        """
        # Bark English speakers
        return [
            "v2/en_speaker_0",
            "v2/en_speaker_1", 
            "v2/en_speaker_2",
            "v2/en_speaker_3",
            "v2/en_speaker_4",
            "v2/en_speaker_5",
            "v2/en_speaker_6",
            "v2/en_speaker_7",
            "v2/en_speaker_8",
            "v2/en_speaker_9",
        ]

    def set_voice(self, voice: str) -> bool:
        """Set active voice
        
        Args:
            voice: Voice name
            
        Returns:
            True if voice was set, False otherwise
        """
        available_voices = self.get_available_voices()
        if voice in available_voices:
            self.voice = voice
            self.config.set("tts.bark.voice", voice)
            self.logger.info(f"Voice set to: {voice}")
            return True
        else:
            self.logger.warning(f"Voice {voice} not available")
            return False

    def get_status(self) -> dict:
        """Get TTS engine status
        
        Returns:
            Status dictionary
        """
        return {
            "engine": "bark",
            "ready": self.is_ready(),
            "speaking": self.is_speaking,
            "model_size": self.model_size,
            "device": self.device,
            "voice": self.voice,
            "available_voices": self.get_available_voices(),
        }
