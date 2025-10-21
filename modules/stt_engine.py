"""
Speech-to-Text engine using Vosk
"""

import json
import threading
from pathlib import Path
from typing import Optional

import pyaudio
import vosk
from PyQt6.QtCore import QObject, QThread, pyqtSignal

from config.config import Config
from utils.logger import ModuleLogger


class STTEngine(QObject):
    """Vosk-based Speech-to-Text engine"""

    # Signals
    wake_word_detected = pyqtSignal()
    speech_recognized = pyqtSignal(str)
    recording_started = pyqtSignal()
    recording_stopped = pyqtSignal()
    model_ready = pyqtSignal(str)

    def __init__(self, config: Config):
        super().__init__()
        self.config = config
        self.logger = ModuleLogger("STTEngine")

        # Configuration
        self.model_path = config.get("stt.model_path", "models/vosk-model-small-ru-0.22")
        self.wake_word = config.get("stt.wake_word", "арвис").lower()
        # Добавляем распространенные варианты произношения, которые может распознать Vosk
        self.wake_word_variants = [self.wake_word, "арвис", "арвіс", "arvis"]
        self.sample_rate = 16000
        self.chunk_size = 1024

        # State
        self.is_recording = False
        self.is_listening_for_wake_word = False
        self.model = None
        self.recognizer = None
        self.audio_stream = None
        self.audio_interface = None

        # Threading
        self.recording_thread = None
        self.wake_word_thread = None

        # Initialize
        self.init_stt()

    def init_stt(self):
        """Initialize Vosk STT model"""
        try:
            self.logger.info("Initializing Vosk STT...")

            # Check if model exists
            model_path = Path(self.model_path)
            if not model_path.exists():
                self.logger.error(f"Vosk model not found at: {model_path}")
                self.logger.info("Please download a Vosk model and update the path in settings")
                return

            # Load model
            self.model = vosk.Model(str(model_path))
            self.recognizer = vosk.KaldiRecognizer(self.model, self.sample_rate)

            # Defer PyAudio initialization to first use to avoid startup crashes
            self.audio_interface = None

            self.logger.info("Vosk STT initialized successfully (PyAudio will init on first use)")

            try:
                self.model_ready.emit(str(model_path))
            except Exception as emit_error:
                self.logger.debug(f"Failed to emit model_ready signal: {emit_error}")

        except Exception as e:
            self.logger.error(f"Failed to initialize STT: {e}")

    def is_ready(self) -> bool:
        """Check if STT engine is ready"""
        return self.model is not None and self.recognizer is not None

    def get_model(self) -> Optional[vosk.Model]:
        """Provide direct access to the underlying Vosk model (if loaded)."""
        return self.model

    def _ensure_audio_interface(self):
        """Lazily initialize PyAudio interface if not yet created."""
        if self.audio_interface is None:
            try:
                # Initialize PyAudio with error handling for Windows
                self.audio_interface = pyaudio.PyAudio()
                self.logger.info("PyAudio interface initialized successfully")
            except Exception as e:
                self.logger.error(f"Failed to initialize audio interface: {e}")
                # Try to provide helpful information
                if "ALSA" in str(e):
                    self.logger.info("ALSA errors are usually harmless on non-Linux systems")
                elif "PortAudio" in str(e):
                    self.logger.error("PortAudio not properly installed. Please check audio system.")
                return False
        return True

    def start_wake_word_detection(self):
        """Start listening for wake word in background"""
        if not self.is_ready():
            self.logger.error("STT engine not ready")
            return

        if self.is_listening_for_wake_word:
            self.logger.warning("Already listening for wake word")
            return

        self.is_listening_for_wake_word = True
        self.wake_word_thread = threading.Thread(target=self._wake_word_loop, daemon=True)
        self.wake_word_thread.start()
        self.logger.info("Started wake word detection")

    def stop_wake_word_detection(self):
        """Stop wake word detection"""
        self.is_listening_for_wake_word = False
        if self.wake_word_thread:
            self.wake_word_thread.join(timeout=1.0)
        self.logger.info("Stopped wake word detection")

    def _wake_word_loop(self):
        """Background loop for wake word detection"""
        try:
            if not self._ensure_audio_interface():
                return
            # Create audio stream for wake word detection
            stream = self.audio_interface.open(
                format=pyaudio.paInt16, channels=1, rate=self.sample_rate, input=True, frames_per_buffer=self.chunk_size
            )

            wake_recognizer = vosk.KaldiRecognizer(self.model, self.sample_rate)

            while self.is_listening_for_wake_word:
                try:
                    data = stream.read(self.chunk_size, exception_on_overflow=False)

                    if wake_recognizer.AcceptWaveform(data):
                        result = json.loads(wake_recognizer.Result())
                        text = result.get("text", "").lower()

                        # Логируем все распознанные фразы для отладки
                        if text:
                            self.logger.debug(f"Wake word loop recognized: '{text}'")

                        # Проверяем все варианты wake word
                        if any(variant in text for variant in self.wake_word_variants):
                            self.logger.info(f"Wake word detected in: '{text}'")
                            self.wake_word_detected.emit()

                except Exception as e:
                    if self.is_listening_for_wake_word:  # Only log if we're still supposed to be listening
                        self.logger.debug(f"Error in wake word detection: {e}")

            stream.close()

        except Exception as e:
            self.logger.error(f"Error in wake word loop: {e}")

    def start_recording(self):
        """Start recording for speech recognition"""
        if not self.is_ready():
            self.logger.error("STT engine not ready")
            return

        if self.is_recording:
            self.logger.warning("Already recording")
            return

        self.is_recording = True
        self.recording_thread = threading.Thread(target=self._recording_loop, daemon=True)
        self.recording_thread.start()
        self.recording_started.emit()
        self.logger.info("Started recording")

    def stop_recording(self):
        """Stop recording"""
        if self.is_recording:
            self.is_recording = False
            if self.recording_thread:
                self.recording_thread.join(timeout=2.0)
            self.recording_stopped.emit()
            self.logger.info("Stopped recording")

    def _recording_loop(self):
        """Main recording loop"""
        try:
            if not self._ensure_audio_interface():
                return
            # Create audio stream for recording
            stream = self.audio_interface.open(
                format=pyaudio.paInt16, channels=1, rate=self.sample_rate, input=True, frames_per_buffer=self.chunk_size
            )

            # Create new recognizer for this session
            session_recognizer = vosk.KaldiRecognizer(self.model, self.sample_rate)

            speech_detected = False
            silence_counter = 0
            total_silence_counter = 0  # Счетчик полной тишины с начала записи
            max_silence = 40  # ~2.5 seconds of silence after speech to stop (увеличено)
            max_total_silence = 160  # ~10 seconds of complete silence from start to stop (увеличено вдвое)

            while self.is_recording:
                try:
                    data = stream.read(self.chunk_size, exception_on_overflow=False)

                    if session_recognizer.AcceptWaveform(data):
                        result = json.loads(session_recognizer.Result())
                        text = result.get("text", "").strip()

                        if text:
                            speech_detected = True
                            silence_counter = 0
                            total_silence_counter = 0
                            self.logger.info(f"Recognized: {text}")
                            self.speech_recognized.emit(text)
                            break  # Stop after recognizing speech
                    else:
                        # Check for partial results to detect speech activity
                        partial_result = json.loads(session_recognizer.PartialResult())
                        partial_text = partial_result.get("partial", "").strip()

                        if partial_text:
                            speech_detected = True
                            silence_counter = 0
                            total_silence_counter = 0
                            self.logger.debug(f"Partial: {partial_text}")
                        else:
                            # Тишина
                            if speech_detected:
                                silence_counter += 1
                                if silence_counter > max_silence:
                                    # Too much silence after detecting speech
                                    self.logger.info("Stopping: silence after speech detected")
                                    break
                            else:
                                # Полная тишина с начала записи
                                total_silence_counter += 1
                                if total_silence_counter > max_total_silence:
                                    # Пользователь ничего не сказал за 5 секунд
                                    self.logger.info("Stopping: no speech detected within timeout")
                                    break

                except Exception as e:
                    if self.is_recording:  # Only log if we're still supposed to be recording
                        self.logger.debug(f"Error in recording loop: {e}")

            # Get final result
            try:
                final_result = json.loads(session_recognizer.FinalResult())
                final_text = final_result.get("text", "").strip()
                if final_text and not speech_detected:
                    self.logger.info(f"Final recognized: {final_text}")
                    self.speech_recognized.emit(final_text)
                elif not speech_detected and not final_text:
                    # Пользователь ничего не сказал
                    self.logger.info("Recording ended with no speech detected")
                    # Эмитируем пустую строку чтобы сигнализировать об отсутствии речи
                    self.speech_recognized.emit("")
            except Exception as e:
                self.logger.debug(f"Error getting final result: {e}")

            stream.close()

        except Exception as e:
            self.logger.error(f"Error in recording loop: {e}")
        finally:
            self.is_recording = False

    def recognize_audio_file(self, file_path: str) -> Optional[str]:
        """Recognize speech from audio file"""
        if not self.is_ready():
            self.logger.error("STT engine not ready")
            return None

        try:
            import wave

            # Open audio file
            wf = wave.open(file_path, "rb")

            # Check audio format
            if wf.getnchannels() != 1 or wf.getsampwidth() != 2 or wf.getframerate() != self.sample_rate:
                self.logger.error("Audio file must be mono, 16-bit, 16kHz")
                return None

            # Create recognizer
            file_recognizer = vosk.KaldiRecognizer(self.model, self.sample_rate)

            # Process audio
            text_parts = []
            while True:
                data = wf.readframes(self.chunk_size)
                if len(data) == 0:
                    break

                if file_recognizer.AcceptWaveform(data):
                    result = json.loads(file_recognizer.Result())
                    text = result.get("text", "").strip()
                    if text:
                        text_parts.append(text)

            # Get final result
            final_result = json.loads(file_recognizer.FinalResult())
            final_text = final_result.get("text", "").strip()
            if final_text:
                text_parts.append(final_text)

            wf.close()

            full_text = " ".join(text_parts).strip()
            self.logger.info(f"File recognition result: {full_text}")
            return full_text if full_text else None

        except Exception as e:
            self.logger.error(f"Error recognizing audio file: {e}")
            return None

    def set_wake_word(self, wake_word: str):
        """Set wake word"""
        self.wake_word = wake_word.lower()
        self.config.set("stt.wake_word", wake_word)
        self.logger.info(f"Wake word set to: {wake_word}")

    def get_audio_devices(self):
        """Get available audio input devices"""
        if not self.audio_interface:
            return []

        devices = []
        try:
            for i in range(self.audio_interface.get_device_count()):
                device_info = self.audio_interface.get_device_info_by_index(i)
                if device_info["maxInputChannels"] > 0:
                    devices.append(
                        {"index": i, "name": device_info["name"], "channels": device_info["maxInputChannels"]}
                    )
        except Exception as e:
            self.logger.error(f"Error getting audio devices: {e}")

        return devices

    def test_microphone(self) -> bool:
        """Test microphone input"""
        try:
            self.logger.info("Testing microphone...")

            # Record for 3 seconds
            stream = self.audio_interface.open(
                format=pyaudio.paInt16, channels=1, rate=self.sample_rate, input=True, frames_per_buffer=self.chunk_size
            )

            frames = []
            for i in range(0, int(self.sample_rate / self.chunk_size * 3)):
                data = stream.read(self.chunk_size)
                frames.append(data)

            stream.close()

            # Check if we got some audio data
            total_audio = b"".join(frames)
            if len(total_audio) > 0:
                self.logger.info("Microphone test successful")
                return True
            else:
                self.logger.error("No audio data received")
                return False

        except Exception as e:
            self.logger.error(f"Microphone test failed: {e}")
            return False

    def cleanup(self):
        """Cleanup STT resources"""
        try:
            self.stop_wake_word_detection()
            self.stop_recording()

            if self.audio_interface:
                self.audio_interface.terminate()

            self.logger.info("STT cleanup complete")

        except Exception as e:
            self.logger.error(f"Error during STT cleanup: {e}")

    def get_status(self) -> dict:
        """Get STT engine status"""
        return {
            "ready": self.is_ready(),
            "recording": self.is_recording,
            "listening_for_wake_word": self.is_listening_for_wake_word,
            "wake_word": self.wake_word,
            "model_path": self.model_path,
            "sample_rate": self.sample_rate,
        }
