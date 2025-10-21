"""
Silero TTS Engine - refactored to inherit from TTSEngineBase
Силеро TTS Движок - рефакторирован для наследования от TTSEngineBase
"""

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import numpy as np
import sounddevice as sd
import soundfile as sf
import torch

# Setup path for imports
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from config.config import Config
from modules.tts_base import TTSEngineBase, TTSStatus, HealthCheckResult
from utils.logger import ModuleLogger


class SileroTTSEngine(TTSEngineBase):
    """Silero TTS engine for speech synthesis"""

    def __init__(self, config: Config, logger: Optional[ModuleLogger] = None):
        """Initialize Silero TTS engine
        
        Args:
            config: Application configuration
            logger: Optional logger instance
        """
        self.config = config
        self.logger = logger or ModuleLogger("SileroTTSEngine")
        self.model = None
        self.sample_rate = config.get("tts.sample_rate", 48000)
        self.voice = config.get("tts.voice", "aidar")
        self.device = config.get("tts.device", "cpu")
        self.is_ready_flag = False
        self._subprocess_available = False
        self.is_speaking = False
        self.current_audio = None
        self.tts_mode = config.get("tts.mode", "realtime")
        self.tts_enabled = config.get("tts.enabled", True)

        # Buffer for streaming mode to avoid word cutoffs
        self.text_buffer = ""
        self.min_buffer_size = 20  # Minimum characters before speaking
        self.word_boundary_chars = [" ", ".", ",", "!", "?", ";", ":", "\n", "\t"]

        # Initialize TTS
        self._init_tts()

    def _init_tts(self):
        """Initialize Silero TTS model"""
        try:
            self.logger.info("Initializing Silero TTS...")

            # Сначала проверим subprocess worker
            worker_path = Path(__file__).parent / "tts_worker_subprocess.py"
            self._subprocess_available = worker_path.exists()

            # Попробуем прямую загрузку Silero
            try:
                # Временно очищаем sys.path от конфликтующих путей
                original_path = sys.path.copy()
                current_dir = os.getcwd()

                # Удаляем все пути, содержащие текущий проект
                filtered_paths = []
                for path in sys.path:
                    path_abs = os.path.abspath(path) if path else ""
                    current_abs = os.path.abspath(current_dir)

                    # Не включаем пути к нашему проекту
                    if not path or path_abs == current_abs or current_abs in path_abs or "Arvis" in path_abs:
                        continue
                    filtered_paths.append(path)

                # Временно заменяем sys.path
                sys.path = filtered_paths

                # Загружаем модель (в разных версиях silero возвращается либо модель, либо кортеж)
                loaded = torch.hub.load(
                    repo_or_dir="snakers4/silero-models",
                    model="silero_tts",
                    language="ru",
                    speaker="v3_1_ru",
                    verbose=False,
                )
                model = loaded[0] if isinstance(loaded, (tuple, list)) else loaded

                # Восстанавливаем sys.path
                sys.path = original_path

                # Тип модели для стат. анализатора неизвестен, приводим к Any
                model_any: Any = model
                model_any.to(self.device)
                self.model = model_any
                self.is_ready_flag = True
                self.logger.info("✓ Silero TTS initialized successfully")

            except Exception as model_error:
                # Восстанавливаем sys.path в любом случае
                sys.path = original_path
                self.logger.warning(f"Direct TTS model loading failed: {model_error}")

                # Fallback - используем только subprocess
                if self._subprocess_available:
                    self.logger.info("Using subprocess-only TTS mode (fallback)")
                    self.is_ready_flag = False  # Прямая модель не загружена
                    self.model = None
                else:
                    raise Exception(f"Neither direct model nor subprocess available: {model_error}")

        except Exception as e:
            self.logger.error(f"Failed to initialize TTS: {e}")
            self.is_ready_flag = False
            self.model = None

    def _map_voice(self, voice: str) -> str:
        """Normalize voice aliases to real Silero speaker ids"""
        if not voice:
            return "aidar"
        v = voice.lower().strip()
        if v in {"ru_v3", "ru-v3", "v3", "default"}:
            return "aidar"
        return v

    def speak(self, text: str, voice: Optional[str] = None):
        """Convert text to speech and play it asynchronously
        
        Args:
            text: Text to synthesize
            voice: Optional voice name
        """
        # Проверяем, включена ли TTS в настройках
        if not self.tts_enabled:
            self.logger.debug("TTS disabled in settings, skipping speech")
            return

        if self.is_speaking:
            self.logger.warning("Already speaking, stopping current playback")
            self.stop()

        from utils.async_manager import task_manager

        def tts_task():
            try:
                self.logger.info(f"Starting TTS for: {text[:50]}...")

                # Если прямая модель не загружена, используем subprocess
                if self.model is None:
                    self.logger.info("Direct model not available, using subprocess")
                    return self._speak_via_subprocess(text, voice)

                # Если модель загружена, используем её
                self.logger.info(f"Using direct model for speech: {text[:50]}...")
                speaker_val: Union[str, Any] = voice if voice is not None else self.voice
                speaker = str(speaker_val) if not isinstance(speaker_val, str) else speaker_val
                speaker = self._map_voice(speaker)

                model_any: Any = self.model
                audio = model_any.apply_tts(text=text, speaker=speaker, sample_rate=self.sample_rate)

                if audio is not None:
                    if torch.is_tensor(audio):
                        audio = audio.cpu().numpy()

                    # Запускаем воспроизведение в отдельном потоке
                    self._play_audio_async(audio)
                    return True
                else:
                    self.logger.error("Failed to generate audio")
                    return False

            except Exception as e:
                self.logger.error(f"Error in TTS: {e}")
                return self._speak_via_subprocess(text, voice)

        # Запускаем TTS асинхронно с уникальным именем
        import time
        unique_task_name = f"tts_speak_{int(time.time() * 1000)}"
        task_manager.run_async(unique_task_name, tts_task)

    def speak_streaming(self, text_chunk: str, voice: Optional[str] = None):
        """Speak text chunk for streaming mode (realtime) with buffering
        
        Args:
            text_chunk: Text chunk to add to buffer
            voice: Optional voice name
        """
        if not self.tts_enabled or self.tts_mode != "realtime":
            return

        # Add chunk to buffer
        self.text_buffer += text_chunk

        # Check if we have enough text and can find a good breaking point
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
                sd.stop()
                self.is_speaking = False
                self.current_audio = None
                self.logger.info("TTS playback stopped")
        except Exception as e:
            self.logger.error(f"Error stopping TTS: {e}")

    def flush_buffer(self, voice: Optional[str] = None):
        """Flush remaining text in buffer (call at end of generation)
        
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
            # Check basic readiness
            if not self.is_ready():
                return HealthCheckResult(
                    healthy=False,
                    message="TTS engine not ready",
                    details={"model_loaded": self.model is not None, "subprocess_available": self._subprocess_available}
                )

            # Check model if available
            if self.model is not None:
                try:
                    # Try a quick TTS generation
                    model_any: Any = self.model
                    audio = model_any.apply_tts(
                        text="тест",
                        speaker=self._map_voice(self.voice),
                        sample_rate=self.sample_rate
                    )
                    if audio is None:
                        return HealthCheckResult(
                            healthy=False,
                            message="TTS audio generation failed",
                            details={"test_audio": None}
                        )
                except Exception as e:
                    return HealthCheckResult(
                        healthy=False,
                        message=f"TTS health check failed: {str(e)[:100]}",
                        details={"error": str(e)[:100]}
                    )

            return HealthCheckResult(
                healthy=True,
                message="TTS engine healthy",
                details={"voice": self.voice, "sample_rate": self.sample_rate, "device": self.device}
            )

        except Exception as e:
            return HealthCheckResult(
                healthy=False,
                message=f"Health check error: {str(e)[:100]}",
                details={"error": str(e)[:100]}
            )

    def is_ready(self) -> bool:
        """Check if TTS engine is ready"""
        # Готов если модель загружена ИЛИ доступен subprocess fallback
        return (self.is_ready_flag and self.model is not None) or self._subprocess_available

    def _play_audio_async(self, audio_data):
        """Play audio asynchronously"""
        import threading

        def play():
            try:
                self.is_speaking = True
                self.current_audio = audio_data

                try:
                    sd.play(audio_data, samplerate=self.sample_rate)
                    sd.wait()  # Wait in separate thread, don't block UI
                except Exception as pe:
                    self.logger.error(f"Audio playback failed: {pe}")

                self.is_speaking = False
                self.current_audio = None

            except Exception as e:
                self.logger.error(f"Error playing audio: {e}")
                self.is_speaking = False

        thread = threading.Thread(target=play, daemon=True)
        thread.start()

    def _speak_via_subprocess(self, text: str, voice: Optional[str] = None, output_filename: Optional[str] = None):
        """Use a dedicated subprocess worker to synthesize speech"""
        try:
            worker_path = Path(__file__).parent / "tts_worker_subprocess.py"
            if not worker_path.exists():
                self.logger.error(f"Subprocess worker not found: {worker_path}")
                return False

            voice = str(voice or self.voice)

            # Ограничиваем длину текста для стабильности
            original_length = len(text)
            if len(text) > 500:
                text = text[:500] + "..."
                self.logger.info(f"Text truncated from {original_length} to {len(text)} chars")

            self.logger.info(f"Starting subprocess TTS: '{text[:30]}...' with voice '{voice}'")

            args = [
                sys.executable,
                str(worker_path),
                "--text",
                text,
                "--voice",
                voice,
                "--sample-rate",
                str(self.sample_rate),
                "--device",
                self.device,
            ]
            # Проброс флага разрешения SAPI
            if bool(self.config.get("tts.sapi_enabled", True)):
                args += ["--sapi-enabled"]
            if output_filename:
                args += ["--output", output_filename]

            # Увеличиваем timeout и улучшаем обработку ошибок
            try:
                self.logger.debug(f"Running subprocess: {' '.join(args[:3])}...")
                result = subprocess.run(
                    args,
                    capture_output=True,
                    text=True,
                    timeout=30,
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
                )

                if result.returncode == 0:
                    self.logger.info("TTS subprocess completed successfully")
                    if result.stdout and result.stdout.strip():
                        self.logger.info(f"TTS subprocess: {result.stdout.strip()}")
                    return True
                else:
                    error_msg = result.stderr.strip() if result.stderr else "Unknown subprocess error"
                    self.logger.error(f"TTS subprocess failed (code {result.returncode}): {error_msg}")
                    return False

            except subprocess.TimeoutExpired:
                self.logger.error("TTS subprocess timed out after 30 seconds")
                return False

        except Exception as e:
            self.logger.error(f"Failed to run TTS subprocess: {e}")
            return False

    def save_to_file(self, text: str, filename: str, voice: Optional[str] = None) -> bool:
        """Save TTS audio to file"""
        # Если прямая модель не загружена, сразу используем сабпроцесс
        if self.model is None:
            self.logger.info("Direct model unavailable, using subprocess to save file")
            return self._speak_via_subprocess(text, voice, output_filename=filename)

        try:
            speaker = str(voice or self.voice)
            speaker = self._map_voice(speaker)

            # Generate audio
            model_any: Any = self.model
            audio = model_any.apply_tts(text=text, speaker=speaker, sample_rate=self.sample_rate)

            if audio is not None:
                # Convert to numpy array if needed
                if torch.is_tensor(audio):
                    audio = audio.cpu().numpy()

                # Save to file
                sf.write(filename, audio, self.sample_rate)
                self.logger.info(f"✓ Audio saved to: {filename}")
                return True
            else:
                self.logger.error("Failed to generate audio for file")
                return False

        except Exception as e:
            self.logger.error(f"Error saving TTS to file: {e}. Trying subprocess fallback...")
            return self._speak_via_subprocess(text, voice, output_filename=filename)

    def get_available_voices(self) -> list:
        """Get list of available voices"""
        return [
            "aidar",  # Male
            "baya",  # Female
            "kseniya",  # Female
            "xenia",  # Female
            "eugene",  # Male
            "ru_v3",  # Default
        ]

    def set_voice(self, voice: str):
        """Set active voice"""
        available_voices = self.get_available_voices()
        if voice in available_voices:
            self.voice = voice
            self.config.set("tts.voice", voice)
            self.logger.info(f"Voice set to: {voice}")
            return True
        else:
            self.logger.error(f"Voice {voice} not available")
            return False
