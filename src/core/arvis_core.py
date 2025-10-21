"""
Core functionality for Arvis AI Assistant
"""

import asyncio
import json
import time
from enum import Enum
from typing import Any, Dict, List, Optional

from PyQt5.QtCore import QObject, QThread, QTimer, pyqtSignal
from PyQt5.QtWidgets import QApplication


class GenerationState(Enum):
    """State machine for message generation"""

    IDLE = "idle"
    GENERATING = "generating"
    REGENERATING = "regenerating"
    CANCELLED = "cancelled"


from config.config import Config
from i18n import _
from modules.calendar_module import CalendarModule
from modules.llm_client import LLMClient
from modules.news_module import NewsModule
from modules.search_module import SearchModule
from modules.stt_engine import STTEngine
from modules.system_control import SystemControlModule
from modules.tts_engine import TTSEngine
from modules.tts_factory import TTSFactory  # NEW: Factory pattern (Days 4-5)
from modules.tts_base import TTSEngineBase  # NEW: Base class for type hints
from modules.wake_word_detector import KaldiWakeWordDetector
from modules.weather_module import WeatherModule
from utils.conversation_history import ConversationHistory
from utils.logger import ModuleLogger
from utils.security import (
    AuditEventType,
    AuditSeverity,
    Permission,
    Role,
    get_audit_logger,
    get_auth_manager,
    get_rbac_manager,
)


class ArvisCore(QObject):
    """Main core class for Arvis functionality"""

    # Signals
    response_ready = pyqtSignal(str)
    partial_response = pyqtSignal(str)
    processing_started = pyqtSignal()
    processing_finished = pyqtSignal()
    status_changed = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)
    voice_activation_detected = pyqtSignal()
    voice_message_recognized = pyqtSignal(str)  # Сигнал для распознанного голосового сообщения
    components_initialized = pyqtSignal()
    stt_model_ready = pyqtSignal(str)
    voice_assets_ready = pyqtSignal()
    tts_engine_switched = pyqtSignal(str)  # NEW: Emits engine type when switched

    def __init__(self, config: Config):
        super().__init__()
        self.config = config
        self.logger = ModuleLogger("ArvisCore")

        # Security & RBAC (v1.5.0+)
        self.rbac_enabled = bool(
            self.config.get("security.rbac.enabled", self.config.get("security.rbac_enabled", False))
        )
        self.rbac = get_rbac_manager() if self.rbac_enabled else None
        self.audit = get_audit_logger(config) if self.config.get("audit.enabled", False) else None
        self.current_user_id = None  # ID текущего пользователя (Day 4 integration)
        self.current_user = None  # Текущий аутентифицированный пользователь

        # Устанавливаем роль по умолчанию если RBAC выключен
        if self.rbac and not self.rbac_enabled:
            self.rbac.set_role(Role.ADMIN)  # Полный доступ если RBAC выключен
        elif self.rbac:
            # Роль по умолчанию из конфига
            default_role_str = str(
                self.config.get("security.rbac.default_role", self.config.get("security.default_role", "user"))
                or "user"
            )
            try:
                self.rbac.set_role(Role[default_role_str.upper()])
            except (KeyError, AttributeError):
                self.rbac.set_role(Role.USER)

        # Core components
        self.llm_client = None
        self.tts_engine = None
        self.stt_engine = None
        self.wake_word_detector = None

        # TTS Factory (Days 4-5: NEW)
        self._tts_factory = TTSFactory()
        self._tts_engine_type: Optional[str] = None  # Track current engine type
        self._available_tts_engines: List[str] = []  # Available engines from config
        self._tts_engine_priority: List[str] = []  # Fallback priority list

        # Modules
        self.weather_module = None
        self.news_module = None
        self.system_control_module = None
        self.calendar_module = None
        self.search_module = None

        # Conversation history manager (с постоянным хранением)
        self.conversation_history_manager = ConversationHistory(config)

        # State
        self.conversation_history = []  # Временная совместимость, будет удалена
        self.is_processing = False
        self.generation_state = GenerationState.IDLE  # State machine для генерации
        self.is_voice_recording = False
        self.is_audio_playback_paused = False
        self._is_tts_playing = False
        self._last_wake_ts = 0.0
        # Источник начала записи: 'none' | 'user' | 'wake'
        self._recording_source = "none"
        # LLM stream/autocontinue state
        self._is_streaming_current = False
        self._stream_buffer_text = ""
        self._auto_continue_attempts = 0
        self._pending_search_results: Optional[Dict[str, Any]] = None
        try:
            self._auto_continue_enabled = bool(self.config.get("llm.auto_continue", True))
        except Exception:
            self._auto_continue_enabled = True
        try:
            # По умолчанию максимум 2 автопродолжения
            ac_max = self.config.get("llm.auto_continue_max_attempts", 2)
            self._auto_continue_max_attempts = ac_max if isinstance(ac_max, int) and ac_max >= 0 else 2
        except Exception:
            self._auto_continue_max_attempts = 2

        # Preloaded acknowledgement phrases cache for instant wake responses
        self._preloaded_ack_cache: Dict[str, List[Any]] = {}
        self._pending_ack_task_id: Optional[str] = None
        self._ack_cache_target = 3
        self._stt_model_ready = False
        self._stt_model_path: Optional[str] = None
        self._voice_assets_ready = False
        self._ready_greeting_pending = True
        self._initial_ack_retry_attempts = 0

        # Async task manager
        from utils.async_manager import task_manager

        self.task_manager = task_manager

        # Initialize components asynchronously
        self.init_components_async()

        # Быстрый статус таймер
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self._update_status_fast)
        self.status_timer.start(7000)  # Каждые ~7 секунд, неблокирующе

        # Таймер для отложенной генерации фраз подтверждения после полной инициализации
        self.ack_init_timer = QTimer()
        self.ack_init_timer.setSingleShot(True)
        self.ack_init_timer.timeout.connect(lambda: self._prime_name_ack_cache_async(initial=True))

        # Периодическая очистка логов/временных файлов
        try:
            from utils.housekeeping import run_periodic_housekeeping

            run_periodic_housekeeping(self.config)  # первый прогон
            self.housekeeping_timer = QTimer()
            self.housekeeping_timer.timeout.connect(lambda: run_periodic_housekeeping(self.config))
            self.housekeeping_timer.start(10 * 60 * 1000)  # каждые 10 минут
        except Exception:
            pass

    def init_components_async(self):
        """Initialize all core components asynchronously"""

        def init_task():
            try:
                self.logger.info("Initializing Arvis core components...")

                # Initialize LLM client (быстро)
                self.llm_client = LLMClient(self.config)
                self.logger.info("LLM client initialized")

                # Initialize TTS engine using Factory pattern (Days 4-5: NEW)
                self.logger.info("Initializing TTS engine using Factory pattern...")
                try:
                    self._build_engine_priority_list()
                    engine_type = self.config.get("tts.default_engine", "silero")
                    
                    # Query server for engine negotiation (if hybrid mode)
                    if self.config.get("auth.use_remote_server", False):
                        server_engine = self._negotiate_engine_with_server()
                        if server_engine:
                            engine_type = server_engine
                            self.logger.info(f"Server negotiated engine: {engine_type}")
                    
                    # Create engine with fallback
                    self.tts_engine = self._create_tts_engine_with_fallback(engine_type)
                    self.logger.info(f"TTS engine initialized: {self._tts_engine_type}")
                except Exception as e:
                    self.logger.error(f"Failed to initialize TTS engine: {e}")
                    # Fallback to basic TTSEngine if factory fails
                    self.tts_engine = TTSEngine(self.config)
                    self._tts_engine_type = "legacy"
                    self.logger.info("TTS engine initialized (fallback to legacy)")
                # Признак проигрывания TTS можно будет интегрировать при добавлении сигналов в TTSEngine

                # Initialize STT engine (может быть медленно)
                stt_duration = 0.0
                stt_start = time.time()
                try:
                    self.status_changed.emit({"stt_loading": "started"})
                except Exception:
                    pass
                # Создаём STT engine и сохраняем сильную ссылку
                stt_instance = STTEngine(self.config)
                stt_duration = time.time() - stt_start

                # Проверяем, что объект не был удалён во время создания
                if stt_instance is None:
                    self.logger.error("STT engine creation returned None")
                    raise RuntimeError("STT engine failed to initialize")

                try:
                    self.status_changed.emit({"stt_loading": "finished", "stt_load_seconds": round(stt_duration, 3)})
                except Exception:
                    pass

                self.logger.info(f"STT engine initialized (load {stt_duration:.2f}s)")

                # Подключаем сигналы ДО присваивания self.stt_engine
                # Распознанная речь → обработка
                stt_instance.speech_recognized.connect(self.process_voice_input)

                # Следим за началом/окончанием записи
                try:
                    stt_instance.recording_started.connect(lambda: self._set_voice_recording(True))
                    stt_instance.recording_stopped.connect(lambda: self._set_voice_recording(False))
                except Exception:
                    pass

                try:
                    stt_instance.model_ready.connect(self._on_stt_model_ready)
                except Exception as connect_error:
                    self.logger.debug(f"Failed to connect STT model_ready signal: {connect_error}")

                # Только после всех подключений присваиваем self.stt_engine
                self.stt_engine = stt_instance
                self.logger.info("STT engine connections established")

                # Initialize Wake Word Detector (для работы с ключевым словом)
                wake_word_engine = str(self.config.get("stt.wake_word_engine", "vosk") or "vosk").lower()
                if wake_word_engine == "porcupine":
                    self.logger.warning(
                        "Picovoice Porcupine wake word detection is no longer supported; falling back to Vosk."
                    )
                    wake_word_engine = "vosk"
                    try:
                        self.config.set("stt.wake_word_engine", "vosk")
                    except Exception:
                        pass

                self.wake_word_detector = None

                if wake_word_engine == "kaldi":
                    self.logger.info("Initializing Kaldi wake word detector...")
                    # Проверяем, что STT engine всё ещё существует
                    if self.stt_engine and hasattr(self.stt_engine, "get_model"):
                        shared_model = self.stt_engine.get_model()
                    else:
                        shared_model = None
                        self.logger.warning("STT engine not available for Kaldi wake word detector")

                    detector = KaldiWakeWordDetector(self.config, shared_model=shared_model)
                    if detector and detector.is_ready():
                        detector.wake_word_detected.connect(self._on_wake_word_detected)
                        self.wake_word_detector = detector
                        self.logger.info("Kaldi wake word detector initialized")
                    else:
                        self.logger.error("Failed to initialize Kaldi wake word detector")
                        if detector:
                            try:
                                detector.cleanup()
                            except Exception:
                                pass

                if not self.wake_word_detector:
                    # Fallback к встроенному детектору в Vosk
                    self.logger.info("Using built-in Vosk wake word detection")
                    if self.stt_engine and hasattr(self.stt_engine, "wake_word_detected"):
                        try:
                            self.stt_engine.wake_word_detected.connect(self._on_wake_word_detected)
                        except Exception as e:
                            self.logger.warning(f"Failed to connect built-in wake word signal: {e}")

                # Initialize modules
                self.init_modules()
                # Конфигурируем голосовую активацию (wake word)
                self._configure_voice_activation()

                return True

            except Exception as e:
                self.logger.error(f"Failed to initialize core components: {e}")
                return False

        def on_init_complete(task_id, result):
            if task_id == "core_init":
                # Отключаем сигналы чтобы избежать повторных вызовов
                try:
                    self.task_manager.task_completed.disconnect(on_init_complete)
                    self.task_manager.task_failed.disconnect(on_init_error)
                except:
                    pass

                if result:
                    self.logger.info("All core components initialized successfully")
                    try:
                        self.components_initialized.emit()
                    except Exception:
                        pass
                else:
                    self.error_occurred.emit("Ошибка инициализации компонентов")

        def on_init_error(task_id, error):
            if task_id == "core_init":
                # Отключаем сигналы чтобы избежать повторных вызовов
                try:
                    self.task_manager.task_completed.disconnect(on_init_complete)
                    self.task_manager.task_failed.disconnect(on_init_error)
                except:
                    pass

                self.logger.error(f"Core initialization failed: {error}")
                self.error_occurred.emit(f"Ошибка инициализации: {error}")

        # Проверяем, не запущена ли уже инициализация
        if not self.task_manager.is_task_running("core_init"):
            self.task_manager.task_completed.connect(on_init_complete)
            self.task_manager.task_failed.connect(on_init_error)
            self.task_manager.run_async("core_init", init_task)
        else:
            self.logger.debug("Core initialization already in progress")

    def _set_voice_recording(self, active: bool):
        """Безопасно установить флаг записи и оповестить UI."""
        try:
            self.is_voice_recording = bool(active)
            # Быстрый пинг статуса
            self.status_changed.emit(
                {"is_recording": self.is_voice_recording, "recording_by_user": self._recording_source == "user"}
            )
        except Exception:
            pass

    def _on_stt_model_ready(self, model_path: str):
        """Handle STT model readiness and notify observers."""
        try:
            self._stt_model_ready = True
            self._stt_model_path = model_path
            self.logger.info(f"STT model ready: {model_path}")
        except Exception as exc:
            self.logger.debug(f"Failed to record STT readiness state: {exc}")

        status_payload = {"stt_model_ready": True, "stt_model_path": model_path, "stt_ready": True}
        try:
            self.status_changed.emit(status_payload)
        except Exception:
            pass

        try:
            self.stt_model_ready.emit(model_path)
        except Exception:
            pass

        try:
            if self.ack_init_timer and not self.ack_init_timer.isActive():
                self.ack_init_timer.start(250)
        except Exception:
            pass

        # Перепроверяем конфигурацию голосовой активации на случай, если она ожидала готовности модели
        try:
            self._configure_voice_activation()
        except Exception as cfg_error:
            self.logger.debug(f"Wake activation reconfig failed after STT ready: {cfg_error}")

        self._maybe_play_ready_greeting()

    def _prime_name_ack_cache_async(self, initial: bool = False):
        """Asynchronously pre-generate quick acknowledgement phrases for TTS."""
        try:
            if not self.tts_engine or not self.tts_engine.is_ready():
                return

            phrases = self._collect_ack_phrases()
            if not phrases:
                return

            max_slots = max(1, min(3, len(phrases)))
            self._ack_cache_target = max_slots
            phrases_to_prepare = phrases[:max_slots]

            # Выясняем, какие фразы ещё не имеют буфера
            needed = [p for p in phrases_to_prepare if len(self._preloaded_ack_cache.get(p, [])) == 0]
            if not needed:
                if initial:
                    self.logger.debug("Acknowledgement cache already primed")
                return

            if self._pending_ack_task_id and self.task_manager.is_task_running(self._pending_ack_task_id):
                return

            import time

            task_id = f"preload_name_ack_{int(time.time() * 1000)}"
            self._pending_ack_task_id = task_id

            def worker():
                engine = self.tts_engine
                if not engine or not hasattr(engine, "preload_phrases"):
                    return {}
                return engine.preload_phrases(needed, limit=len(needed))

            def on_complete(tid, result):
                if tid != task_id:
                    return
                try:
                    self.task_manager.task_completed.disconnect(on_complete)
                except Exception:
                    pass
                try:
                    self.task_manager.task_failed.disconnect(on_fail)
                except Exception:
                    pass
                self._pending_ack_task_id = None

                success = False
                if isinstance(result, dict):
                    for text, clips in result.items():
                        if not clips:
                            continue
                        cache_list = self._preloaded_ack_cache.setdefault(text, [])
                        cache_list.extend(clips)
                        # Ограничиваем до двух клипов на фразу, чтобы не разрастался кеш
                        if len(cache_list) > 2:
                            del cache_list[:-2]
                        success = True
                    total = sum(len(v) for v in self._preloaded_ack_cache.values())
                    self.logger.info(f"Preloaded acknowledgement cache updated ({total} clip(s) available)")
                else:
                    self.logger.debug("Acknowledgement preload returned no data")

                if initial:
                    self._handle_initial_ack_ready(success)
                else:
                    self._schedule_ack_cache_refill()

            def on_fail(tid, error):
                if tid != task_id:
                    return
                try:
                    self.task_manager.task_completed.disconnect(on_complete)
                except Exception:
                    pass
                try:
                    self.task_manager.task_failed.disconnect(on_fail)
                except Exception:
                    pass
                self._pending_ack_task_id = None
                self.logger.debug(f"Ack preload task failed: {error}")
                if initial:
                    self._handle_initial_ack_ready(False)
                else:
                    self._schedule_ack_cache_refill()

            self.task_manager.task_completed.connect(on_complete)
            self.task_manager.task_failed.connect(on_fail)
            self.task_manager.run_async(task_id, worker)

        except Exception as exc:
            self.logger.debug(f"Ack preload scheduling error: {exc}")
            self._pending_ack_task_id = None

    def _schedule_ack_cache_refill(self):
        """Schedule cache refill when fewer than target clips remain."""
        try:
            target = getattr(self, "_ack_cache_target", 3)
            total_cached = sum(len(v) for v in self._preloaded_ack_cache.values())
            if total_cached >= target:
                return
            if self._pending_ack_task_id and self.task_manager.is_task_running(self._pending_ack_task_id):
                return
            QTimer.singleShot(500, lambda: self._prime_name_ack_cache_async())
        except Exception as exc:
            self.logger.debug(f"Ack cache refill scheduling error: {exc}")

    def _handle_initial_ack_ready(self, success: bool):
        """React to the very first acknowledgement preload completion."""
        try:
            if success:
                self._voice_assets_ready = True
                self._initial_ack_retry_attempts = 0
                self.logger.info("Wake acknowledgement phrases prepared successfully")
                try:
                    self.voice_assets_ready.emit()
                except Exception:
                    pass
                try:
                    self.status_changed.emit({"voice_assets_ready": True})
                except Exception:
                    pass
                self._schedule_ack_cache_refill()
            else:
                self._voice_assets_ready = False
                self._initial_ack_retry_attempts += 1
                self.logger.warning("Wake acknowledgement preload failed; scheduling retry")
                if self._initial_ack_retry_attempts <= 3:
                    QTimer.singleShot(2000, lambda: self._prime_name_ack_cache_async(initial=True))
                else:
                    self.logger.error("Wake acknowledgement preload exceeded retry limit")
        except Exception as exc:
            self.logger.debug(f"Initial ack handling error: {exc}")

        # Попытка проговорить приветствие после загрузки активов (или после неудачи)
        force_greeting = not success and self._initial_ack_retry_attempts > 0
        self._maybe_play_ready_greeting(force=force_greeting)

    def _maybe_play_ready_greeting(self, force: bool = False):
        """Speak the ready greeting once everything is loaded."""
        if not self._ready_greeting_pending:
            return

        if not self._stt_model_ready:
            return

        engine = self.tts_engine
        if not engine or not engine.is_ready():
            # Подождём и попробуем ещё раз
            QTimer.singleShot(1000, lambda: self._maybe_play_ready_greeting(force))
            return

        if not force and not self._voice_assets_ready:
            return

        try:
            phrase = "Готов к работе"
            cfg_value = self.config.get("voice.ready_phrase", phrase)
            if isinstance(cfg_value, str) and cfg_value.strip():
                phrase = cfg_value.strip()
        except Exception:
            phrase = "Готов к работе"

        self.logger.info(f"Announcing readiness phrase: '{phrase}'")
        try:
            engine.speak(phrase)
            try:
                self.status_changed.emit({"ready_greeting_played": True})
            except Exception:
                pass
        except Exception as exc:
            self.logger.error(f"Failed to speak ready greeting: {exc}")
        finally:
            self._ready_greeting_pending = False

    def _take_preloaded_ack_audio(self, phrase: str):
        """Fetch pre-generated audio for a specific phrase if available."""
        try:
            queue = self._preloaded_ack_cache.get(phrase)
            if queue:
                audio = queue.pop(0)
                if not queue:
                    self._preloaded_ack_cache.pop(phrase, None)
                return audio
        except Exception as exc:
            self.logger.debug(f"Ack cache retrieval error: {exc}")
        return None

    def _collect_ack_phrases(self) -> List[str]:
        """Собрать список коротких фраз подтверждения для быстрой реакции."""
        phrases: List[str] = []
        try:
            ack_phrase = str(self.config.get("voice.wake_ack", "Слушаю") or "").strip()
        except Exception:
            ack_phrase = "Слушаю"
        if ack_phrase:
            phrases.append(ack_phrase)

        default_responses = ["Да?", "Слушаю вас", "Чем могу помочь?"]
        try:
            raw_responses_cfg = self.config.get("voice.name_responses", default_responses)
        except Exception:
            raw_responses_cfg = default_responses

        if isinstance(raw_responses_cfg, (list, tuple)):
            responses_iter = [str(item) for item in raw_responses_cfg]
        elif isinstance(raw_responses_cfg, str):
            responses_iter = [seg.strip() for seg in raw_responses_cfg.split(",") if seg.strip()]
        else:
            responses_iter = default_responses

        for item in responses_iter:
            phrase = str(item or "").strip()
            if phrase and phrase not in phrases:
                phrases.append(phrase)

        return phrases

    def _configure_voice_activation(self):
        """Запустить или остановить слежение за ключевым словом на основе настроек."""
        try:
            enabled = bool(self.config.get("modules.voice_activation_enabled", False))
        except Exception:
            enabled = False

        try:
            # Получаем текущий движок для распознавания wake word
            wake_word_engine = str(self.config.get("stt.wake_word_engine", "vosk") or "vosk").lower()
            if wake_word_engine == "porcupine":
                wake_word_engine = "vosk"

            # Если используем внешний движок wake word (Kaldi)
            if wake_word_engine == "kaldi" and self.wake_word_detector:
                engine_label = "Kaldi"

                if enabled:
                    if self.wake_word_detector.is_ready():
                        self.wake_word_detector.start_detection()
                        self.logger.info(f"{engine_label} wake word detection enabled")
                    else:
                        self.logger.warning(f"{engine_label} wake word detector not ready")
                else:
                    self.wake_word_detector.stop_detection()
                    self.logger.info(f"{engine_label} wake word detection disabled")

            # Если используем встроенный в Vosk
            elif self.stt_engine and self.stt_engine.is_ready():
                if enabled:
                    # Запускаем прослушивание wake word через Vosk
                    self.stt_engine.start_wake_word_detection()
                    self.logger.info("Vosk wake word detection enabled")
                else:
                    # Отключаем если было включено
                    self.stt_engine.stop_wake_word_detection()
                    self.logger.info("Vosk wake word detection disabled")
            else:
                self.logger.warning("No suitable wake word detector available")

        except Exception as e:
            self.logger.debug(f"Voice activation config error: {e}")

    def _on_wake_word_detected(self):
        """Обработка события активации голосом с защитами от ложных срабатываний."""
        try:
            now = time.time()
            # Кулдаун 2 секунды между активациями
            if now - getattr(self, "_last_wake_ts", 0.0) < 2.0:
                self.logger.debug("Wake ignored: cooldown active")
                return
            self._last_wake_ts = now

            # Не активируемся во время проигрывания TTS или активной обработки
            if self._is_tts_playing or self.is_processing:
                self.logger.debug("Wake ignored: TTS playing or processing in progress")
                return

            self.logger.info("Wake word detected, preparing acknowledgement")

            # ОСТАНАВЛИВАЕМ СЛЕЖЕНИЕ ЗА WAKE WORD ПЕРЕД ОТВЕТОМ
            try:
                # Определяем текущий движок wake word
                wake_word_engine = str(self.config.get("stt.wake_word_engine", "vosk") or "vosk").lower()
                if wake_word_engine == "porcupine":
                    wake_word_engine = "vosk"

                if wake_word_engine == "kaldi" and self.wake_word_detector:
                    self.wake_word_detector.stop_detection()
                    self.logger.debug("Kaldi wake word detection stopped before TTS")
                elif self.stt_engine:
                    self.stt_engine.stop_wake_word_detection()
                    self.logger.debug("Vosk wake word detection stopped before TTS")
            except Exception as e:
                self.logger.debug(f"Error stopping wake word detection: {e}")
                pass

            # Сообщаем UI о триггере (можно подсветить микрофон)
            try:
                self.voice_activation_detected.emit()
            except Exception:
                pass

            # Произнесём короткую фразу подтверждения, затем начнём запись
            ack = str(self.config.get("voice.wake_ack", "Слушаю"))
            self._speak_and_start_recording_after_tts(ack)
        except Exception as e:
            self.logger.debug(f"Wake handler error: {e}")

    def process_voice_input(self, text: str):
        """Process recognized voice input"""
        self.logger.info(f"Voice input recognized: '{text}'")

        # Останавливаем запись
        try:
            if self.stt_engine and self.is_voice_recording:
                self.stt_engine.stop_recording()
                self._set_voice_recording(False)
        except Exception:
            pass

        # Обработка пустого ввода (пользователь молчал)
        if not text.strip():
            self.logger.info("No speech detected from user, restarting wake word detection")
            # Перезапуск wake word listening после короткой задержки
            QTimer.singleShot(300, lambda: self._restart_wake_listening_if_enabled())
            return

        # Проверяем, не является ли текст просто именем ассистента
        try:
            wake_word = str(self.config.get("stt.wake_word", "арвис")).lower()
            # Добавляем варианты распознавания
            wake_variants = [wake_word, "джарвис", "арвіс", "jarvis"]
            text_lower = text.lower().strip()

            # Улучшенное сравнение: убираем все пробелы, знаки препинания и т.д.
            import re

            text_clean = re.sub(r"[^\w]", "", text_lower).lower()

            self.logger.debug(f"Comparing: '{text_lower}' (clean: '{text_clean}') with wake variants")

            # Проверяем все варианты
            is_name_only = any(
                text_lower == variant or text_clean == re.sub(r"[^\w]", "", variant).lower()
                for variant in wake_variants
            )

            if is_name_only:
                self.logger.info("Detected name-only call, responding...")
                self._respond_to_name_only()
                return
        except Exception as e:
            self.logger.error(f"Error checking wake word: {e}")

        # Эмитируем сигнал для добавления сообщения пользователя в UI и обрабатываем
        self.voice_message_recognized.emit(text)
        self.process_message(text)
        # Перезапуск wake word после обработки (мягкая задержка)
        QTimer.singleShot(600, lambda: self._restart_wake_listening_if_enabled())

    def _restart_wake_listening_if_enabled(self):
        """Перезапуск слежения за wake word, если включено в настройках."""
        try:
            if not bool(self.config.get("modules.voice_activation_enabled", False)):
                return

            # Не запускаем, если уже идёт запись
            if self.is_voice_recording:
                return

            # Определяем текущий движок wake word
            wake_word_engine = str(self.config.get("stt.wake_word_engine", "vosk") or "vosk").lower()
            if wake_word_engine == "porcupine":
                wake_word_engine = "vosk"

            # Запускаем соответствующий детектор
            if wake_word_engine == "kaldi" and self.wake_word_detector:
                self.logger.debug("Restarting Kaldi wake word detection")
                self.wake_word_detector.start_detection()
            elif self.stt_engine:
                self.logger.debug("Restarting Vosk wake word detection")
                self.stt_engine.start_wake_word_detection()

        except Exception as e:
            self.logger.debug(f"Error restarting wake word detection: {e}")
            pass

    def _respond_to_name_only(self):
        """Ответить на обращение только по имени и продолжить слушать."""
        try:
            phrases = self._collect_ack_phrases()
            if not phrases:
                phrases = ["Да?", "Слушаю вас", "Чем могу помочь?"]

            cached_options = [p for p in phrases if len(self._preloaded_ack_cache.get(p, [])) > 0]

            import random

            if cached_options:
                response = random.choice(cached_options)
            else:
                response = random.choice(phrases)

            # Говорим короткую фразу и начинаем слушать снова
            self.logger.info(f"Will respond with phrase: '{response}'")
            self._speak_and_start_recording_after_tts(response)

            self.logger.info(f"Responded to name-only call with: {response}")

        except Exception as e:
            self.logger.error(f"Error responding to name only: {e}")
            # При ошибке пытаемся просто начать слушать
            self.toggle_voice_recording(source="wake")

    def init_modules(self):
        """Initialize functional modules"""
        try:
            # Weather module
            self.weather_module = WeatherModule(self.config)

            # News module
            self.news_module = NewsModule(self.config)

            # System control module
            self.system_control_module = SystemControlModule(self.config)

            # Calendar module
            self.calendar_module = CalendarModule(self.config)

            # Web search module
            try:
                self.search_module = SearchModule(self.config)
                if not self.search_module.is_enabled():
                    self.logger.info("Search module initialized but currently disabled")
            except Exception as search_error:
                self.search_module = None
                self.logger.error(f"Failed to initialize search module: {search_error}")

            self.logger.info("All modules initialized")

        except Exception as e:
            self.logger.error(f"Failed to initialize modules: {e}")

    def _update_status_fast(self):
        """Лёгкий монитор ресурсов и предупреждения в UI"""
        try:
            import psutil

            cpu = psutil.cpu_percent(interval=None)
            mem = psutil.virtual_memory().percent

            def _as_int(v, d):
                try:
                    if isinstance(v, int):
                        return v
                    if isinstance(v, str) and v.strip().isdigit():
                        return int(v)
                except Exception:
                    pass
                return d

            warn_cpu = _as_int(self.config.get("performance.cpu_warn_percent", 85), 85)
            warn_mem = _as_int(self.config.get("performance.mem_warn_percent", 85), 85)
            # Сообщаем в UI только при превышении порогов, не чаще 1 раза в 30с
            now = time.time()
            if cpu >= warn_cpu:
                last = getattr(self, "_last_cpu_warn", 0)
                if now - last > 30:
                    self._emit_status_message(f"⚠️ Высокая загрузка CPU: {cpu:.0f}%")
                    self._last_cpu_warn = now
            if mem >= warn_mem:
                last = getattr(self, "_last_mem_warn", 0)
                if now - last > 30:
                    self._emit_status_message(f"⚠️ Мало свободной памяти: {mem:.0f}% занято")
                    self._last_mem_warn = now
        except Exception:
            pass

    def _emit_status_message(self, text: str):
        """Отправка системного сообщения в панель статуса через сигнал error_occurred как инфо."""
        try:
            # Используем error_occurred для всплывашки, но с мягким текстом
            self.error_occurred.emit(text)
        except Exception:
            pass

    def process_message(self, message: str, is_regeneration: bool = False):
        """Process user message with performance monitoring

        Args:
            message: User message to process
            is_regeneration: If True, do not add message to history (for retry functionality)
        """
        # RBAC: Проверка прав на использование чата (v1.5.0+)
        if self.rbac and not self.rbac.has_permission(Permission.CHAT_USE):
            error_msg = "❌ У вас нет прав для использования чата"
            self.logger.warning(f"Permission denied: CHAT_USE for role {self.rbac.get_role()}")
            if self.audit:
                self.audit.log_event(
                    AuditEventType.PERMISSION_DENIED,
                    "Attempted to use chat without permission",
                    username=self.current_user.username if self.current_user else None,
                    details={"required_permission": "CHAT_USE"},
                    success=False,
                    severity=AuditSeverity.WARNING,
                )
            self.error_occurred.emit(error_msg)
            return

        # Проверка состояния генерации для предотвращения конкурентности
        if self.generation_state == GenerationState.GENERATING:
            self.logger.warning(
                f"Generation already in progress (state: {self.generation_state}), ignoring new message"
            )
            # Проверяем, не завис ли предыдущий запрос
            if hasattr(self, "_processing_start_time"):
                elapsed_time = time.time() - self._processing_start_time
                if elapsed_time > 10.0:
                    self.logger.warning(f"Force-resetting stuck generation after {elapsed_time:.1f}s")
                    self._force_reset_processing_state()
                    self.error_occurred.emit("Предыдущий запрос был прерван. Повторите попытку.")
                else:
                    self.logger.info(f"Still generating (elapsed: {elapsed_time:.1f}s), ignoring")
                    self.error_occurred.emit(
                        f"Запрос обрабатывается ({elapsed_time:.0f}с). Подождите или попробуйте позже."
                    )
                    return
            else:
                self.logger.warning("Generation state inconsistent, force-resetting")
                self._force_reset_processing_state()
                self.error_occurred.emit("Сброс состояния. Повторите запрос.")

        from utils.performance_monitor import performance_monitor

        start_time = time.time()

        # Устанавливаем состояние генерации
        if is_regeneration:
            self.generation_state = GenerationState.REGENERATING
            self.logger.info(f"Starting regeneration for message: {message[:50]}...")
        else:
            self.generation_state = GenerationState.GENERATING
            self.logger.info(f"Starting new generation for message: {message[:50]}...")

        # Сброс счетчиков автопродолжения и буфера на новый запрос
        self._auto_continue_attempts = 0
        self._stream_buffer_text = ""
        self._is_streaming_current = False

        self.is_processing = True
        self._processing_start_time = start_time  # Отслеживаем время начала

        # Очищаем предыдущий timeout timer если есть
        if hasattr(self, "_timeout_timer") and self._timeout_timer:
            try:
                self._timeout_timer.stop()
                self._timeout_timer.deleteLater()
                self._timeout_timer = None
            except Exception:
                pass

        self.processing_started.emit()

        try:
            # Add to conversation history только если это НЕ регенерация
            if not is_regeneration:
                self.logger.info(f"Processing message: {message}")
                self.conversation_history_manager.add_message("user", message)
                # Обновляем временный список для обратной совместимости
                self.conversation_history = self.conversation_history_manager.get_all()
            else:
                self.logger.info(f"Regenerating response for: {message}")
                # При регенерации НЕ добавляем сообщение пользователя повторно

            # Сбрасываем результаты веб-поиска, ожидая новую обработку
            self._pending_search_results = None

            # Check if this is a module command (non-AI)
            module_response = self.handle_module_commands(message)
            if module_response:
                self.response_ready.emit(module_response)
                # Сохраняем ответ модуля в истории
                self.conversation_history_manager.add_message(
                    "assistant", module_response, metadata={"source": "module"}
                )
                self.conversation_history = self.conversation_history_manager.get_all()
                # Finish processing immediately for module commands
                self.is_processing = False
                self.generation_state = GenerationState.IDLE  # Сбрасываем состояние
                self.processing_finished.emit()
                # Перезапускаем wake word detection после модульной команды
                # Увеличенная задержка (3 сек) дает TTS время озвучить ответ
                QTimer.singleShot(3000, lambda: self._restart_wake_listening_if_enabled())
                performance_monitor.record_operation_time("module_command", time.time() - start_time)
            else:
                # Process with LLM (время будет измерено в process_with_llm)
                self.process_with_llm(message)

        except Exception as e:
            self.logger.error(f"Error processing message: {e}")
            self.error_occurred.emit(f"Ошибка обработки: {e}")
            # Ensure proper cleanup
            self._force_reset_processing_state()
            performance_monitor.record_operation_time("message_error", time.time() - start_time)

    def handle_module_commands(self, message: str) -> Optional[str]:
        """Handle non-AI module commands with RBAC checks (v1.5.0+)"""
        message_lower = message.lower()

        # Weather commands - ПРИОРИТЕТ: специализированный модуль
        if any(word in message_lower for word in ["погода", "температура", "weather"]):
            # RBAC: Проверка прав на модуль погоды
            if self.rbac and not self.rbac.can_use_module("weather"):
                self.logger.warning(f"Permission denied: MODULE_WEATHER for role {self.rbac.get_role()}")
                if self.audit:
                    self.audit.log_event(
                        AuditEventType.PERMISSION_DENIED,
                        "Attempted to use weather module without permission",
                        username=self.current_user.username if self.current_user else None,
                        success=False,
                        severity=AuditSeverity.INFO,
                    )
                return "❌ У вас нет прав для использования модуля погоды (требуется роль User или выше)"

            if self.weather_module:
                return self.weather_module.get_weather()

        # News commands - ПРИОРИТЕТ: специализированный модуль
        if any(word in message_lower for word in ["новости", "news"]):
            # RBAC: Проверка прав на модуль новостей
            if self.rbac and not self.rbac.can_use_module("news"):
                self.logger.warning(f"Permission denied: MODULE_NEWS for role {self.rbac.get_role()}")
                if self.audit:
                    self.audit.log_event(
                        AuditEventType.PERMISSION_DENIED,
                        "Attempted to use news module without permission",
                        username=self.current_user.username if self.current_user else None,
                        success=False,
                        severity=AuditSeverity.INFO,
                    )
                return "❌ У вас нет прав для использования модуля новостей (требуется роль User или выше)"

            if self.news_module:
                return self.news_module.get_news()

        # System control commands - ПРИОРИТЕТ: специализированный модуль
        if any(word in message_lower for word in ["запусти", "открой", "включи", "выключи"]):
            if self.system_control_module:
                # Проверка прав будет внутри SystemControlModule
                return self.system_control_module.execute_command(message)

        # Audio control commands - ПРИОРИТЕТ: специализированный модуль
        if any(word in message_lower for word in ["громкость", "звук", "музыка"]):
            if self.system_control_module:
                return self.system_control_module.control_audio(message)

        # Web search commands - FALLBACK: только если специализированные модули не сработали
        if self.search_module and self.search_module.is_enabled():
            try:
                if self.search_module.should_handle(message):
                    search_payload = self.search_module.search(message)
                    if search_payload and search_payload.get("results"):
                        self._pending_search_results = search_payload
                        self.logger.info(
                            f"Collected {len(search_payload['results'])} web results for query '{search_payload['query']}'"
                        )
                        # Продолжаем обработку через LLM, чтобы сформировать ответ с источниками
                        return None
                    elif search_payload and search_payload.get("error"):
                        self.logger.warning(f"Search module error: {search_payload.get('error')}")
                        self.error_occurred.emit(_("Не удалось выполнить веб-поиск. Проверьте соединение."))
                        return None
                    else:
                        self.logger.info("Search module returned no results")
                        self.error_occurred.emit(_("Мне не удалось найти актуальные источники в сети."))
                        return None
            except Exception as search_exception:
                self.logger.error(f"Search module failure: {search_exception}")
                self.error_occurred.emit(_("Ошибка веб-поиска: {error}").format(error=search_exception))
                return None

        return None

    def process_with_llm(self, message: str):
        """Process message with LLM"""
        if not self.llm_client:
            self.error_occurred.emit("LLM клиент не инициализирован")
            return

        try:
            search_payload = self._pending_search_results

            # Prepare context
            context = self.build_context(search_payload)

            # Decide streaming or full-response mode
            use_stream = bool(self.config.get("llm.stream", True))

            # Автоподбор модели по ресурсам при 'auto'
            try:
                if getattr(self.llm_client, "default_model", None) in (None, "", "auto"):
                    import psutil

                    mem_gb = psutil.virtual_memory().total / (1024**3)
                    # Пример эвристики: >24GB — крупные, >12GB — средние, иначе маленькие
                    if mem_gb >= 24:
                        preferred = ["qwen2:7b", "mistral:7b", "llama3:8b", "phi3:medium"]
                    elif mem_gb >= 12:
                        preferred = ["phi3:mini", "gemma2:2b", "llama3:3b", "qwen2:1.5b"]
                    else:
                        preferred = ["qwen2:0.5b", "phi3:mini", "tinyllama:1.1b"]
                    available = []
                    try:
                        available = self.llm_client.get_available_models()
                    except Exception:
                        pass
                    for m in preferred:
                        if m in available:
                            if hasattr(self.llm_client, "set_model"):
                                self.llm_client.set_model(m)
                            break
            except Exception:
                pass

            # Run LLM request in a background thread to avoid blocking UI
            if use_stream:
                # Check if stream_response method exists
                if not hasattr(self.llm_client, "stream_response"):
                    self.logger.error("LLM client does not have stream_response method, falling back to regular mode")
                    use_stream = False

            if use_stream:
                worker = _LLMStreamWorker(
                    llm_client=self.llm_client,
                    message=message,
                    context=context,
                    history=self.conversation_history_manager.get_recent(6),  # Последние 6 для контекста
                )
            else:
                worker = _LLMWorker(
                    llm_client=self.llm_client,
                    message=message,
                    context=context,
                    history=self.conversation_history_manager.get_recent(6),  # Последние 6 для контекста
                )

            # Keep a reference to prevent GC
            self._current_llm_worker = worker
            self._is_streaming_current = bool(use_stream)

            # Set timeout for worker to prevent hanging (configurable)
            try:
                wt = self.config.get("llm.worker_timeout_ms", 45000)
                worker_timeout_ms = wt if isinstance(wt, int) and wt > 0 else 45000
            except Exception:
                worker_timeout_ms = 45000
            self._worker_timeout_ms = worker_timeout_ms

            self._timeout_timer = QTimer()
            self._timeout_timer.setSingleShot(True)
            self._timeout_timer.timeout.connect(self._check_worker_timeout)
            self._timeout_timer.start(worker_timeout_ms)

            def on_success(resp: str):
                try:
                    if resp and resp.strip():
                        enriched_resp = resp
                        if search_payload and search_payload.get("results"):
                            enriched_resp = self._append_search_sources(resp, search_payload)

                        self.response_ready.emit(enriched_resp)

                        metadata = {"source": "llm", "model": getattr(self.llm_client, "default_model", "unknown")}
                        if search_payload and search_payload.get("results"):
                            metadata["search_results"] = search_payload.get("results")

                        # Сохраняем ответ LLM в историю
                        self.conversation_history_manager.add_message("assistant", enriched_resp, metadata=metadata)
                        self.conversation_history = self.conversation_history_manager.get_all()
                        self.logger.info(f"LLM response received successfully ({len(resp)} chars)")
                    else:
                        self.error_occurred.emit("Не удалось получить ответ от LLM")
                        self.logger.warning("Empty response from LLM")
                finally:
                    self._pending_search_results = None
                    # Используем новый метод для надежной очистки состояния
                    self._cleanup_processing_state()

            def on_error(err: str):
                try:
                    self.logger.error(f"Error processing with LLM (worker): {err}")
                    self.error_occurred.emit(f"Ошибка LLM: {err}")
                finally:
                    self._pending_search_results = None
                    # Используем новый метод для надежной очистки состояния
                    self._cleanup_processing_state()

            if use_stream:
                # Accumulate chunks; also forward partials
                buffer = {"text": ""}
                self._stream_buffer_text = ""

                def on_chunk(chunk: str):
                    if not chunk:
                        return
                    buffer["text"] += chunk
                    # Дублируем в общий буфер для возможного автопродолжения/таймаута
                    self._stream_buffer_text = buffer["text"]
                    # Перезапуск таймаута на каждый чанк (по желанию из конфига отдельный таймаут)
                    try:
                        sct = self.config.get("llm.stream_chunk_timeout_ms", None)
                        chunk_timeout = (
                            sct if isinstance(sct, int) and sct > 0 else getattr(self, "_worker_timeout_ms", 45000)
                        )
                        if hasattr(self, "_timeout_timer") and self._timeout_timer:
                            self._timeout_timer.stop()
                            self._timeout_timer.start(chunk_timeout)
                    except Exception:
                        pass
                    self.partial_response.emit(buffer["text"])  # emit accumulated for safety

                def on_done():
                    # Проверяем что получили хотя бы какой-то текст
                    final_text = buffer["text"].strip()
                    if not final_text:
                        self.logger.warning("Stream completed but no text was received")
                        self.error_occurred.emit("Получен пустой ответ от LLM. Попробуйте повторить запрос.")
                        # Очистка состояния стрима
                        self._is_streaming_current = False
                        self._stream_buffer_text = ""
                        return

                    # Эвристика: если ответ оборван (нет завершающего знака) и включено автопродолжение
                    if (
                        self._auto_continue_enabled
                        and self._auto_continue_attempts < self._auto_continue_max_attempts
                        and self._should_auto_continue(final_text)
                    ):
                        try:
                            self._auto_continue_attempts += 1
                            # Отправляем первую часть в UI и фиксируем в истории
                            try:
                                self.response_ready.emit(final_text)
                            except Exception:
                                pass
                            # Сохраняем часть ответа (будет продолжение)
                            self.conversation_history_manager.add_message(
                                "assistant",
                                final_text,
                                metadata={"source": "llm_partial", "part": self._auto_continue_attempts},
                            )
                            self.conversation_history = self.conversation_history_manager.get_all()
                            self.logger.info(
                                f"Auto-continue #{self._auto_continue_attempts}: detected truncated ending, scheduling continuation"
                            )
                            # Мягко уведомляем UI
                            self.error_occurred.emit("✍️ Продолжаю генерацию...")
                            # Завершаем текущий цикл обработки и сразу запускаем продолжение
                            self._cleanup_processing_state()
                            # Небольшая задержка для UI
                            QTimer.singleShot(100, lambda: self.process_message("Продолжи"))
                            return
                        except Exception as e:
                            self.logger.debug(f"Auto-continue scheduling failed: {e}")

                    self.logger.info(f"Stream completed successfully with {len(final_text)} characters")
                    # Очистка признаков стрима
                    self._is_streaming_current = False
                    self._stream_buffer_text = ""
                    on_success(final_text)  # finalize

                # Подписываемся на сигналы стрим-воркера (_LLMStreamWorker)
                if isinstance(worker, _LLMStreamWorker):
                    worker.chunk.connect(on_chunk)
                    worker.done.connect(on_done)

                    # Оборачиваем ошибку стрима, чтобы попытаться автопродолжить частичный текст
                    def _stream_on_error_bridge(err: str):
                        txt = (buffer.get("text") or "").strip()
                        if (
                            txt
                            and self._auto_continue_enabled
                            and self._auto_continue_attempts < self._auto_continue_max_attempts
                        ):
                            self._auto_continue_attempts += 1
                            self.logger.warning(
                                f"LLM stream error; auto-continue attempt #{self._auto_continue_attempts}"
                            )
                            try:
                                self.response_ready.emit(txt)
                            except Exception:
                                pass
                            try:
                                self.conversation_history.append({"role": "assistant", "content": txt})
                            except Exception:
                                pass
                            self._force_reset_processing_state()
                            self.error_occurred.emit("⚠️ Ошибка стрима. Продолжаю генерацию...")
                            QTimer.singleShot(150, lambda: self.process_message("Продолжи"))
                        else:
                            on_error(err)

                    worker.error.connect(_stream_on_error_bridge)
            else:
                # Подписываемся на сигналы обычного воркера (_LLMWorker)
                if isinstance(worker, _LLMWorker):
                    # Для нестримового режима добавляем автопродолжение в on_success
                    def _non_stream_success_bridge(resp: str):
                        try:
                            if resp and resp.strip():
                                text = resp.strip()
                                if (
                                    self._auto_continue_enabled
                                    and not self._is_streaming_current
                                    and self._auto_continue_attempts < self._auto_continue_max_attempts
                                    and self._should_auto_continue(text)
                                    and ("Ошибка" not in text)
                                    and ("Не удается" not in text)
                                    and ("Извините" not in text)
                                ):
                                    self._auto_continue_attempts += 1
                                    self.response_ready.emit(text)
                                    self.conversation_history.append({"role": "assistant", "content": text})
                                    self.logger.info(
                                        f"Non-stream auto-continue #{self._auto_continue_attempts} scheduled"
                                    )
                                    self._cleanup_processing_state()
                                    QTimer.singleShot(120, lambda: self.process_message("Продолжи"))
                                    return
                        except Exception:
                            pass
                        on_success(resp)

                    worker.success.connect(_non_stream_success_bridge)
                    worker.error.connect(on_error)
            worker.start()

        except Exception as e:
            self.logger.error(f"Error scheduling LLM processing: {e}")
            self.error_occurred.emit(f"Ошибка LLM: {e}")

    def _append_search_sources(self, response_text: str, search_payload: Dict[str, Any]) -> str:
        """Append formatted search sources to the assistant response."""
        try:
            results = []
            raw_results = search_payload.get("results") if isinstance(search_payload, dict) else None
            if isinstance(raw_results, list):
                results = [r for r in raw_results if isinstance(r, dict) and r.get("link")]
            if not results:
                return response_text

            lines: List[str] = []
            lines.append(_("🔎 Источники:"))
            for idx, item in enumerate(results, start=1):
                title = (item.get("title") or item.get("display_link") or item.get("link") or "").strip()
                link = (item.get("link") or "").strip()
                display_link = (item.get("display_link") or "").strip()
                snippet = (item.get("snippet") or "").strip()

                if not title:
                    title = link or display_link or _("Источник")

                bullet = f"{idx}. {title}"
                if display_link and display_link != link:
                    bullet += f" — {display_link}"
                if link:
                    bullet += f" ({link})"
                lines.append(bullet)

                if snippet:
                    lines.append(f"   {snippet}")

            base_text = (response_text or "").rstrip()
            appendix = "\n".join(lines).strip()
            if not base_text:
                return appendix
            return f"{base_text}\n\n{appendix}"
        except Exception as exc:
            self.logger.debug(f"Failed to append search sources: {exc}")
            return response_text

    def build_context(self, search_payload: Optional[Dict[str, Any]] = None) -> str:
        """Build context information for LLM"""
        context_parts = []

        # User information
        user_name = self.config.get("user.name", "Пользователь")
        user_city = self.config.get("user.city", "")

        context_parts.append(f"Пользователя зовут {user_name}.")
        if user_city:
            context_parts.append(f"Пользователь находится в городе {user_city}.")

        # Available modules
        available_modules = []
        if self.weather_module:
            available_modules.append("погода")
        if self.news_module:
            available_modules.append("новости")
        if self.system_control_module:
            available_modules.append("управление компьютером")
        if self.calendar_module:
            available_modules.append("календарь")

        if available_modules:
            context_parts.append(f"Доступные модули: {', '.join(available_modules)}.")

        # System info
        context_parts.append("Ты - Arvis, ИИ-ассистент. Отвечай дружелюбно и полезно.")

        if search_payload and search_payload.get("context"):
            context_parts.append(
                "Используй свежие результаты поиска ниже, чтобы дать точный ответ с упоминанием источника."
            )
            context_parts.append(search_payload["context"])

        return " ".join(context_parts)

    # process_voice_input реализован выше с перезапуском wake listening

    def toggle_voice_recording(self, source: str = "user"):
        """Toggle voice recording state.

        source: 'user' (кнопка) | 'wake' (ключевое слово) — влияет на UI-индикацию.
        """
        if not self.stt_engine:
            self.error_occurred.emit("STT движок не инициализирован")
            return

        if self.is_voice_recording:
            self.logger.info("Stopping voice recording")
            self.stt_engine.stop_recording()
            self.is_voice_recording = False
            self._recording_source = "none"
            self.logger.info("Voice recording stopped")
        else:
            self.logger.info(f"Starting voice recording (source: {source})")
            self.stt_engine.start_recording()
            self.is_voice_recording = True
            self._recording_source = "user" if source == "user" else "wake"
            self.logger.info("Voice recording started")

    def _speak_and_start_recording_after_tts(self, phrase: str):
        """Озвучить фразу подтверждения и после завершения TTS начать запись (wake)."""
        try:
            self.logger.info(f"Speak and start recording: '{phrase}'")

            if self.tts_engine and self.tts_engine.is_ready():
                clip_used = False

                # Проверяем предзагруженный кеш
                preloaded = self._take_preloaded_ack_audio(phrase)
                if preloaded is not None:
                    self.logger.info(f"Using preloaded acknowledgement audio for: '{phrase}'")
                    clip_used = self.tts_engine.play_audio_array(preloaded)
                    if clip_used:
                        self._schedule_ack_cache_refill()

                if not clip_used:
                    self.logger.info(f"Synthesizing acknowledgement phrase: '{phrase}'")
                    self.tts_engine.speak(phrase)
                    # При следующем вызове попробуем пополнить кеш
                    self._schedule_ack_cache_refill()

                # Ожидаем окончания TTS неблокирующе
                def _poll():
                    try:
                        engine = self.tts_engine
                        is_speaking = getattr(engine, "is_speaking", False) if engine else False

                        if engine and is_speaking:
                            QTimer.singleShot(100, _poll)
                        else:
                            self.logger.info("TTS completed, starting recording")
                            # УВЕЛИЧЕННАЯ задержка перед началом записи чтобы микрофон точно не услышал остаток TTS
                            # 500мс достаточно для завершения проигрывания и очистки аудио буфера
                            QTimer.singleShot(500, lambda: self.toggle_voice_recording(source="wake"))
                    except Exception as e:
                        self.logger.error(f"Error in TTS polling: {e}")
                        # Даже при ошибке используем увеличенную задержку
                        QTimer.singleShot(500, lambda: self.toggle_voice_recording(source="wake"))

                self.logger.debug("Starting TTS completion polling")
                QTimer.singleShot(150, _poll)
            else:
                self.logger.warning("TTS engine not ready, starting recording directly")
                self.toggle_voice_recording(source="wake")
        except Exception as e:
            self.logger.error(f"Ack+record error: {e}")
            self.toggle_voice_recording(source="wake")

    def toggle_audio_playback(self):
        """Toggle audio playback state"""
        self.is_audio_playback_paused = not self.is_audio_playback_paused

        if self.tts_engine:
            if self.is_audio_playback_paused:
                self.tts_engine.pause()
            else:
                self.tts_engine.resume()

        status = "приостановлено" if self.is_audio_playback_paused else "возобновлено"
        self.logger.info(f"Audio playback {status}")

    def set_assistant_feedback(self, message: str, feedback: str) -> bool:
        """Сохранить пользовательскую оценку для ответа ассистента."""
        if not message:
            self.logger.warning("Empty message passed for feedback")
            return False

        if not self.conversation_history_manager:
            self.logger.warning("Conversation history manager is not available for feedback")
            return False

        saved = self.conversation_history_manager.set_message_feedback(message, feedback)
        if saved:
            self.logger.info(f"Assistant feedback '{feedback}' saved")
            return True

        self.logger.warning("Failed to match assistant message for feedback saving")
        return False

    def clear_conversation_history(self):
        """Clear conversation history (с архивацией текущей сессии)"""
        # Очищаем через менеджер (автоматически архивирует)
        self.conversation_history_manager.clear()
        self.conversation_history = []
        # Также сбрасываем состояние обработки для чистого старта
        if self.is_processing:
            self._force_reset_processing_state()
        self.logger.info("Conversation history cleared and archived")

    def _force_reset_processing_state(self):
        """Принудительно сбросить состояние обработки при зависании"""
        try:
            # Очищаем timeout timer
            if hasattr(self, "_timeout_timer") and self._timeout_timer:
                try:
                    self._timeout_timer.stop()
                    self._timeout_timer.deleteLater()
                    self._timeout_timer = None
                except Exception:
                    pass

            # Остановить текущий worker если есть
            if hasattr(self, "_current_llm_worker") and self._current_llm_worker:
                try:
                    if hasattr(self._current_llm_worker, "terminate"):
                        self._current_llm_worker.terminate()
                    if hasattr(self._current_llm_worker, "quit"):
                        self._current_llm_worker.quit()
                except Exception as e:
                    self.logger.debug(f"Error terminating worker: {e}")
                finally:
                    self._current_llm_worker = None

            # Сбросить флаги состояния
            self.is_processing = False
            self.generation_state = GenerationState.IDLE  # Сбрасываем состояние генерации
            if hasattr(self, "_processing_start_time"):
                delattr(self, "_processing_start_time")

            # Уведомить UI о завершении обработки
            self.processing_finished.emit()

            # Перезапускаем wake word detection после принудительного сброса
            # Увеличенная задержка (3 сек) дает TTS время озвучить ответ
            QTimer.singleShot(3000, lambda: self._restart_wake_listening_if_enabled())

            self.logger.info("Processing state forcibly reset")

        except Exception as e:
            self.logger.error(f"Error during force reset: {e}")
            # В любом случае сбрасываем флаги
            self.is_processing = False
            self._current_llm_worker = None
            # Попытка перезапуска wake word даже при ошибке
            try:
                QTimer.singleShot(3000, lambda: self._restart_wake_listening_if_enabled())
            except Exception:
                pass

    def _cleanup_processing_state(self):
        """Обычная очистка состояния после завершения обработки"""
        try:
            self.is_processing = False
            self.generation_state = GenerationState.IDLE  # Сбрасываем состояние генерации
            if hasattr(self, "_processing_start_time"):
                delattr(self, "_processing_start_time")
            self._current_llm_worker = None
            self.processing_finished.emit()

            # Перезапускаем wake word detection после завершения обработки
            # Увеличенная задержка (3 сек) дает TTS время озвучить ответ перед началом прослушивания
            QTimer.singleShot(3000, lambda: self._restart_wake_listening_if_enabled())
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
            # Fallback to force reset
            self._force_reset_processing_state()

    def _check_worker_timeout(self):
        """Проверить таймаут worker и принудительно сбросить если необходимо"""
        if self.is_processing and hasattr(self, "_current_llm_worker"):
            if self._current_llm_worker is not None:
                # Если это стрим и у нас есть частичный текст — пробуем автопродолжение
                if (
                    self._is_streaming_current
                    and self._stream_buffer_text.strip()
                    and self._auto_continue_enabled
                    and self._auto_continue_attempts < self._auto_continue_max_attempts
                ):
                    partial = self._stream_buffer_text.strip()
                    self._auto_continue_attempts += 1
                    self.logger.warning(f"LLM worker timeout; auto-continue attempt #{self._auto_continue_attempts}")
                    # Завершаем текущий воркер и фиксируем частичный текст в истории
                    self._force_reset_processing_state()
                    try:
                        self.conversation_history.append({"role": "assistant", "content": partial})
                    except Exception:
                        pass
                    # Мягкое уведомление и запуск продолжения
                    self.error_occurred.emit("⏱️ Таймаут. Продолжаю генерацию...")
                    # Очистим буфер и признак стрима, новый запуск создаст свои значения
                    self._stream_buffer_text = ""
                    self._is_streaming_current = False
                    QTimer.singleShot(150, lambda: self.process_message("Продолжи"))
                    return

                # Иначе — обычный сброс и уведомление
                self.logger.warning("LLM worker timeout detected, forcing reset")
                self._force_reset_processing_state()
                self.error_occurred.emit(
                    "⏱️ Время ожидания ответа истекло (45с). Попробуйте сократить запрос или повторить позже."
                )

    def cancel_current_request(self):
        """Cancel current request if any"""
        if self.is_processing:
            self.logger.info("User cancelled current request")
            self._force_reset_processing_state()
            self.error_occurred.emit("❌ Запрос отменён пользователем.")
        else:
            self.logger.info("No active request to cancel")

    def get_last_user_message(self) -> Optional[str]:
        """Получить последнее сообщение пользователя из истории"""
        for message in reversed(self.conversation_history):
            if message.get("role") == "user":
                return message.get("content")
        return None

    def get_last_assistant_message(self) -> Optional[str]:
        """Получить последний ответ ассистента из истории"""
        for message in reversed(self.conversation_history):
            if message.get("role") == "assistant":
                return message.get("content")
        return None

    def regenerate_last_response(self) -> bool:
        """Regenerate the last assistant response

        This method:
        1. Removes the last assistant message from history
        2. Gets the last user message
        3. Re-processes it without adding to history (is_regeneration=True)

        Returns:
            bool: True if regeneration started successfully, False otherwise
        """
        try:
            # Проверяем, можем ли мы регенерировать
            if self.generation_state != GenerationState.IDLE:
                self.logger.warning(f"Cannot regenerate: wrong state {self.generation_state}")
                return False

            # Получаем последнее сообщение пользователя
            last_user_msg = self.get_last_user_message()
            if not last_user_msg:
                self.logger.warning("Cannot regenerate: no user message found")
                self.error_occurred.emit("⚠️ Не найден последний запрос для повтора")
                return False

            # Удаляем последний ответ ассистента из истории
            last_assistant_msg = self.get_last_assistant_message()
            if last_assistant_msg:
                # Используем новый метод remove_last_message
                removed = self.conversation_history_manager.remove_last_message(role="assistant")
                if removed:
                    self.logger.info("Removed last assistant message for regeneration")
                    # Обновляем локальную копию истории
                    self.conversation_history = self.conversation_history_manager.get_all()
                else:
                    self.logger.warning("Failed to remove last assistant message")

            # Запускаем регенерацию с флагом is_regeneration=True
            self.logger.info(f"Starting regeneration for: {last_user_msg[:50]}...")
            self.process_message(last_user_msg, is_regeneration=True)
            return True

        except Exception as e:
            self.logger.error(f"Error during regeneration: {e}")
            self.error_occurred.emit(f"Ошибка регенерации: {e}")
            return False

    def update_status_fast(self):
        """Update status information without blocking UI"""

        def status_task():
            try:
                # Быстрая проверка статуса
                ollama_connected = self.llm_client.is_connected() if self.llm_client else False
                tts_ready = self.tts_engine.is_ready() if self.tts_engine else False
                stt_ready = self.stt_engine.is_ready() if self.stt_engine else False

                return {
                    "model": self.config.get("llm.default_model", "Неизвестно"),
                    "ollama_connected": ollama_connected,
                    "tts_ready": tts_ready,
                    "stt_ready": stt_ready,
                    "is_processing": self.is_processing,
                    "is_recording": self.is_voice_recording,
                    "playback_paused": self.is_audio_playback_paused,
                }
            except Exception as e:
                self.logger.error(f"Status update error: {e}")
                return None

        def on_status_ready(task_id, status_data):
            if task_id == "status_update" and status_data:
                self.status_changed.emit(status_data)

        # Проверяем, есть ли уже активная задача
        if not self.task_manager.is_task_running("status_update"):
            self.task_manager.task_completed.connect(on_status_ready)
            self.task_manager.run_async("status_update", status_task)

    # Дубликаты toggle_audio_playback и _check_worker_timeout удалены (см. верхние реализации)

    def shutdown(self):
        """Shutdown Arvis core"""
        self.logger.info("Shutting down Arvis core...")

        try:
            # Сохраняем историю разговоров
            if hasattr(self, "conversation_history_manager"):
                self.conversation_history_manager.shutdown()

            # Stop timers
            if self.status_timer:
                self.status_timer.stop()

            # Stop voice recording
            if self.stt_engine and self.is_voice_recording:
                self.stt_engine.stop_recording()

            # Stop TTS
            if self.tts_engine:
                self.tts_engine.stop()

            # Cleanup modules
            if self.weather_module:
                self.weather_module.cleanup()
            if self.news_module:
                self.news_module.cleanup()
            if self.system_control_module:
                self.system_control_module.cleanup()
            if self.calendar_module:
                self.calendar_module.cleanup()

            self.logger.info("Arvis core shutdown complete")

        except Exception as e:
            self.logger.error(f"Error during shutdown: {e}")

    def set_current_user(self, user_id: Optional[str]):
        """Set current user for all modules (Phase 2 Day 4)

        Args:
            user_id: User ID from authentication system, None for guest
        """
        try:
            self.current_user_id = user_id
            self.logger.info(f"Set current user: {user_id or 'Guest'}")

            # Propagate to RBAC
            if self.rbac:
                self.rbac.set_current_user(user_id)

            # Propagate to modules that need user context
            if self.calendar_module and hasattr(self.calendar_module, "set_current_user"):
                self.calendar_module.set_current_user(user_id)
                self.logger.debug("Calendar module user updated")

            if self.search_module and hasattr(self.search_module, "set_current_user"):
                self.search_module.set_current_user(user_id)
                self.logger.debug("Search module user updated")

            if self.system_control_module and hasattr(self.system_control_module, "set_current_user"):
                self.system_control_module.set_current_user(user_id)
                self.logger.debug("System control module user updated")

            # Audit log
            if self.audit and user_id:
                self.audit.log_event(
                    event_type=AuditEventType.LOGIN_SUCCESS,
                    action=f"User set in ArvisCore: {user_id}",
                    user_id=user_id,
                    severity=AuditSeverity.INFO,
                )

        except Exception as e:
            self.logger.error(f"Failed to set current user: {e}")

    def _should_auto_continue(self, text: str) -> bool:
        """Эвристика: считать, что ответ оборван и его стоит продолжить.

        Критерии:
        - нет завершающего знака (., !, ?, …, ") и
        - текст достаточно длинный (>= 60 символов), чтобы исключить очень короткие ответы.
        """
        try:
            t = (text or "").rstrip()
            if len(t) < 60:
                return False
            good_endings = (".", "!", "?", "…", "\u2026", "\u00BB", '"', "'", ")", "]", "}")
            # Часто обрывается на запятой, двоеточии и переносе строки
            bad_endings = (",", ";", ":", "—", "-", "\\")
            if t.endswith(good_endings):
                return False
            if t.endswith(bad_endings) or t[-1].isalnum():
                return True
            # По умолчанию — не продолжаем
            return False
        except Exception:
            return False

    def get_system_info(self) -> Dict[str, Any]:
        """Get system information"""
        return {
            "version": "1.0.0",
            "llm_model": self.config.get("llm.default_model"),
            "ollama_url": self.config.get("llm.ollama_url"),
            "user_name": self.config.get("user.name"),
            "modules_active": {
                "weather": self.weather_module is not None,
                "news": self.news_module is not None,
                "system_control": self.system_control_module is not None,
                "calendar": self.calendar_module is not None,
            },
        }

    # ========== TTS Factory Methods (Days 4-5) ==========

    def _negotiate_engine_with_server(self) -> Optional[str]:
        """Query server for preferred TTS engine (hybrid system).
        
        Currently a placeholder. Will be implemented to query:
        GET /api/client/engine-preference
        
        Returns: engine type string or None if unavailable
        """
        try:
            self.logger.debug("Querying server for engine preference...")
            # TODO: Implement server API call when Client API extended
            # For now: return None (use local config)
            return None
        except Exception as e:
            self.logger.warning(f"Server engine negotiation failed: {e}")
            return None

    def _build_engine_priority_list(self) -> None:
        """Build fallback priority list from config.
        
        Priority: configured default → available engines
        """
        self._available_tts_engines = self._tts_factory.list_available_engines()
        
        # Primary engine from config
        primary = self.config.get("tts.default_engine", "silero")
        
        # Others as fallback
        others = [e for e in self._available_tts_engines if e != primary]
        
        # Build priority list
        self._tts_engine_priority = [primary] + others
        self.logger.info(f"TTS engine priority: {self._tts_engine_priority}")

    def _create_tts_engine_with_fallback(self, engine_type: str) -> TTSEngineBase:
        """Create TTS engine with fallback to alternatives.
        
        Args:
            engine_type: Primary engine type to try
            
        Returns:
            TTSEngineBase instance
            
        Raises:
            RuntimeError: If all engines fail to initialize
        """
        # Try primary first, then fallback list
        engines_to_try = [engine_type] + self._tts_engine_priority
        
        for engine in engines_to_try:
            try:
                self.logger.info(f"Attempting to create {engine} TTS engine...")
                
                # Create engine via factory
                engine_obj = self._tts_factory.create_engine(engine, self.config)
                
                # Run health check
                try:
                    health = engine_obj.health_check()
                    if not health.healthy:
                        self.logger.warning(f"{engine} health check failed: {health.message}")
                        continue
                except Exception as hc_error:
                    self.logger.warning(f"Health check for {engine} failed: {hc_error}")
                    continue
                
                # Success!
                self._tts_engine_type = engine
                self.logger.info(f"✅ Successfully initialized {engine} TTS engine")
                return engine_obj
                
            except Exception as e:
                self.logger.warning(f"Failed to initialize {engine}: {e}")
                continue
        
        # All engines failed
        raise RuntimeError("Could not initialize any TTS engine!")

    async def switch_tts_engine_async(self, new_engine_type: str) -> bool:
        """Switch to different TTS engine at runtime.
        
        Args:
            new_engine_type: Engine type to switch to (e.g., "bark", "silero")
            
        Returns:
            True if switch successful, False otherwise
        """
        try:
            self.logger.info(f"Switching TTS engine: {self._tts_engine_type} → {new_engine_type}")
            
            # Check if new engine available
            if not self._tts_factory.is_engine_available(new_engine_type):
                self.logger.error(f"Engine {new_engine_type} not available")
                return False
            
            # Stop current engine if speaking
            try:
                if self.tts_engine and hasattr(self.tts_engine, "get_status"):
                    status = self.tts_engine.get_status()
                    if status and hasattr(status, "value"):
                        if status.value in ["SPEAKING", "INITIALIZING"]:
                            await self.tts_engine.stop()
            except Exception as stop_error:
                self.logger.warning(f"Failed to stop current engine: {stop_error}")
            
            # Create new engine
            new_engine = self._tts_factory.create_engine(new_engine_type, self.config)
            
            # Run health check
            try:
                health = new_engine.health_check()
                if not health.healthy:
                    self.logger.error(f"{new_engine_type} health check failed: {health.message}")
                    return False
            except Exception as hc_error:
                self.logger.error(f"Health check for {new_engine_type} failed: {hc_error}")
                return False
            
            # Switch
            self.tts_engine = new_engine
            self._tts_engine_type = new_engine_type
            self.logger.info(f"✅ Successfully switched to {new_engine_type}")
            
            # Emit signal for UI update
            try:
                self.tts_engine_switched.emit(new_engine_type)
            except Exception:
                pass
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to switch engine: {e}")
            return False


class _LLMWorker(QThread):
    """Worker thread to perform LLM requests without blocking UI."""

    success = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, llm_client: LLMClient, message: str, context: str, history: list):
        super().__init__()
        self._llm = llm_client
        self._message = message
        self._context = context
        self._history = history

    def run(self):
        try:
            resp = self._llm.get_response(self._message, self._context, self._history)
            # Ensure string type to keep signal typing consistent
            if resp is None:
                self.success.emit("")
            else:
                self.success.emit(str(resp))
        except Exception as e:
            self.error.emit(str(e))


class _LLMStreamWorker(QThread):
    """Worker thread for streaming LLM responses chunk-by-chunk."""

    chunk = pyqtSignal(str)
    done = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, llm_client: LLMClient, message: str, context: str, history: list):
        super().__init__()
        self._llm = llm_client
        self._message = message
        self._context = context
        self._history = history

    def run(self):
        try:
            for part in self._llm.stream_response(self._message, self._context, self._history):
                if part is None:
                    continue
                # Emit the latest chunk (could be empty on errors/timeouts)
                if part:
                    self.chunk.emit(str(part))
            self.done.emit()
        except Exception as e:
            self.error.emit(str(e))
