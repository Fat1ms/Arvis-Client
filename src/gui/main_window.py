"""
Main window for Arvis application
"""

from pathlib import Path
from typing import Optional

from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtSvgWidgets import QSvgWidget
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QSizePolicy,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from config.config import Config
from i18n import I18N, _
from i18n.i18n import apply_to_widget_tree
from utils.logger import ModuleLogger
from utils.update_checker import UpdateChecker
from version import get_full_title

from ..core.arvis_core import ArvisCore
from .chat_history_dialog import ChatHistoryDialog
from .chat_panel import ChatPanel
from .floating_notification import FloatingNotification
from .settings_dialog import SettingsDialog
from .status_panel import StatusPanel
from .update_dialog import UpdateCheckThread, UpdateNotificationDialog


class MainWindow(QMainWindow):
    """Main application window"""

    stt_ready = pyqtSignal(str)
    voice_assets_ready = pyqtSignal()

    def __init__(self, config: Config):
        super().__init__()
        self.config = config
        self.logger = ModuleLogger("MainWindow")
        self.arvis_core = None
        self.settings_dialog = None
        self.floating_notification = None
        self._stt_popup_shown = False
        self.current_user_id = None  # Will be set after successful authentication
        self.ollama_manager = None  # Will be initialized if autostart enabled
        
        # Система авто-обновлений
        self.update_checker = UpdateChecker()
        self.update_check_thread = None

        self.init_ui()
        # Start Ollama if autostart enabled
        if self.config.get("startup.autostart_ollama", False):
            QTimer.singleShot(500, self.start_ollama_if_needed)
        # Проверка обновлений при запуске (отложенная)
        if self.config.get("auto_update.enabled", False) and self.config.get("auto_update.notify_on_startup", True):
            QTimer.singleShot(3000, self.check_for_updates_background)
        # НЕ инициализируем ArvisCore автоматически - это будет сделано из main.py после логина
        # Старая логика: QTimer.singleShot(1000, self.init_arvis_core_delayed)

    def init_ui(self):
        """Initialize user interface"""
        self.setWindowTitle(get_full_title())
        # Фиксированный размер окна - нельзя растягивать
        self.setFixedSize(1080, 720)

        # Remove default title bar and add custom one
        self.setWindowFlags(Qt.FramelessWindowHint)  # type: ignore[attr-defined]
        self.create_title_bar()

        # Center window
        self.center_window()

        # Create main widget with title bar
        main_widget = QWidget()
        self.setCentralWidget(main_widget)

        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Add title bar
        main_layout.addWidget(self.title_bar)
        # Add thin separator under the title bar so the decorative line is never overlapped by buttons
        if hasattr(self, "title_separator"):
            main_layout.addWidget(self.title_separator)

        # Create central widget for content
        central_widget = QWidget()

        # Create panels without splitter to avoid any resizing artifacts
        self.chat_panel = ChatPanel(self.config, external_input_bar=True)
        self.status_panel = StatusPanel(self.config)

        # Enforce fixed widths explicitly
        self.chat_panel.setFixedWidth(700)
        self.status_panel.setFixedWidth(300)

        # Content layout (no splitter)
        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        content_layout.addWidget(self.chat_panel)
        content_layout.addWidget(self.status_panel)
        central_widget.setLayout(content_layout)

        # Add content to main layout (give central area stretch to push bottom bar to the very bottom)
        main_layout.addWidget(central_widget, 1)

        # Добавляем нижнюю панель управления на всю ширину окна с небольшими отступами
        try:
            input_frame = self.chat_panel.get_input_frame()
            if input_frame is not None:
                input_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
                bottom_wrapper = QWidget()
                bottom_layout = QHBoxLayout()
                # Небольшие отступы ~5px от краёв окна (слева/справа и снизу)
                bottom_layout.setContentsMargins(5, 0, 5, 5)
                bottom_layout.addWidget(input_frame)
                bottom_wrapper.setLayout(bottom_layout)
                bottom_wrapper.setContentsMargins(0, 0, 0, 0)
                # Добавляем без выравнивания: в QVBoxLayout элемент после центральной части окажется внизу
                main_layout.addWidget(bottom_wrapper)
        except Exception as e:
            self.logger.error(f"Failed to attach bottom input panel: {e}")
        main_widget.setLayout(main_layout)

        # Connect signals
        self.connect_signals()

        # Apply styles
        self.apply_styles()

        # Floating notification overlay (after central widgets are in place)
        try:
            self.floating_notification = FloatingNotification(self)
            self.floating_notification.hide()
        except Exception as exc:
            self.logger.debug(f"Failed to initialize floating notification: {exc}")

    def center_window(self):
        """Center window on screen"""
        from PyQt6.QtWidgets import QApplication

        screen = QApplication.primaryScreen()
        if screen is None:
            return
        try:
            geom = screen.availableGeometry()
        except Exception:
            try:
                geom = screen.geometry()
            except Exception:
                return
        size = self.frameGeometry()
        size.moveCenter(geom.center())
        self.move(size.topLeft())

    def create_title_bar(self):
        """Create custom title bar"""
        self.title_bar = QWidget()
        self.title_bar.setFixedHeight(32)  # Оптимальная высота для кнопок
        self.title_bar.setStyleSheet(
            """
            QWidget#title_bar {
                background-color: rgb(43, 43, 43);
            }
            QLabel {
                background-color: transparent;
                border: none;
            }
            QPushButton {
                background-color: transparent;
                border: none;
            }
        """
        )
        self.title_bar.setObjectName("title_bar")

        # Title bar layout с отступами от границ
        title_layout = QHBoxLayout()
        title_layout.setContentsMargins(10, 4, 4, 4)  # Слегка симметричные отступы
        title_layout.setSpacing(3)  # Интервал между элементами
        title_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)  # type: ignore[attr-defined]

        # Title text
        self.title_label = QLabel(get_full_title())
        self.title_label.setStyleSheet(
            """
            QLabel {
                color: white;
                font-weight: bold;
                font-size: 12px;
                border: none;
            }
        """
        )

        title_layout.addWidget(self.title_label)
        title_layout.addStretch()

        # Window control buttons
        self.minimize_btn = QPushButton("─")
        self.maximize_btn = QPushButton("□")
        self.close_btn = QPushButton("×")

        # Button styles - компактные кнопки с отступом от границы
        button_style = """
            QPushButton {
                background-color: rgb(43, 43, 43);
                color: rgb(100, 100, 100);
                border: none;
                font-size: 11px;
                font-weight: bold;
                min-width: 24px;
                max-width: 24px;
                min-height: 24px;
                max-height: 24px;
                border-radius: 3px;
                margin: 1px;
            }
            QPushButton:hover {
                background-color: rgb(60, 60, 60);
                color: white;
            }
            QPushButton:pressed {
                background-color: rgb(30, 30, 30);
            }
        """

        # Close button special style (red on hover)
        close_style = """
            QPushButton {
                background-color: rgb(43, 43, 43);
                color: rgb(100, 100, 100);
                border: none;
                font-size: 11px;
                font-weight: bold;
                min-width: 24px;
                max-width: 24px;
                min-height: 24px;
                max-height: 24px;
                border-radius: 3px;
                margin: 1px;
            }
            QPushButton:hover {
                background-color: rgb(200, 50, 50);
                color: white;
            }
            QPushButton:pressed {
                background-color: rgb(180, 30, 30);
            }
        """

        self.minimize_btn.setStyleSheet(button_style)
        self.maximize_btn.setStyleSheet(button_style)
        self.close_btn.setStyleSheet(close_style)

        # Connect buttons
        self.minimize_btn.clicked.connect(self.showMinimized)
        self.maximize_btn.clicked.connect(self.toggle_maximize)
        self.close_btn.clicked.connect(self._on_close_clicked)

        title_layout.addWidget(self.minimize_btn)
        title_layout.addWidget(self.maximize_btn)
        title_layout.addWidget(self.close_btn)

        self.title_bar.setLayout(title_layout)

        # Make title bar draggable
        self.title_bar.mousePressEvent = self.title_bar_mouse_press  # type: ignore[assignment]
        self.title_bar.mouseMoveEvent = self.title_bar_mouse_move  # type: ignore[assignment]

        # Добавляем отдельную разделительную линию под заголовком,
        # чтобы декоративная линия не перекрывалась кнопками
        # (будет добавлена в основной лэйаут рядом с title_bar)
        self.title_separator = QFrame()
        self.title_separator.setFixedHeight(1)
        self.title_separator.setFrameShape(QFrame.NoFrame)
        self.title_separator.setStyleSheet("background-color: rgb(60, 60, 60); border: none;")

    def toggle_maximize(self):
        """Toggle window maximize/restore"""
        if self.isMaximized():
            self.showNormal()
            self.maximize_btn.setText("□")
        else:
            self.showMaximized()
            self.maximize_btn.setText("❐")

    def _on_close_clicked(self) -> None:
        """Close main window from title bar button click."""
        self.close()

    def title_bar_mouse_press(self, event):
        """Handle title bar mouse press"""
        if event.button() == Qt.LeftButton:  # type: ignore[attr-defined]
            self.drag_pos = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def title_bar_mouse_move(self, event):
        """Handle title bar mouse move"""
        if event.buttons() == Qt.LeftButton and hasattr(self, "drag_pos"):  # type: ignore[attr-defined]
            self.move(event.globalPos() - self.drag_pos)
            event.accept()

    def init_arvis_core(self):
        """Initialize Arvis core functionality"""
        try:
            self.arvis_core = ArvisCore(self.config)
            self.logger.info("Arvis core initialized successfully")

            # Connect core to UI
            self.chat_panel.set_arvis_core(self.arvis_core)
            self.status_panel.set_arvis_core(self.arvis_core)

            # Пробрасываем изменения статуса для мгновенного индикатора микрофона в ChatPanel
            try:
                self.arvis_core.status_changed.connect(self._handle_status_changed)
                self.arvis_core.stt_model_ready.connect(self._on_stt_model_ready)
                self.arvis_core.voice_assets_ready.connect(self._on_voice_assets_ready)
            except Exception:
                pass

        except Exception as e:
            self.logger.error(f"Failed to initialize Arvis core: {e}")

    def init_arvis_core_with_progress(self, progress_callback=None):
        """Initialize Arvis core with progress updates for loading screen"""
        try:
            if progress_callback:
                progress_callback("Инициализация ядра системы...", 60)

            self.init_arvis_core()

            if progress_callback:
                progress_callback("Ядро системы готово", 65)

            return True

        except Exception as e:
            self.logger.error(f"Failed to initialize Arvis core: {e}")
            return False

    def warmup_llm(self):
        """Warmup LLM after login for faster first response"""
        try:
            if not self.arvis_core or not self.arvis_core.llm_client:
                self.logger.warning("Cannot warmup LLM: core or client not initialized")
                return

            from utils.llm_warmup import LLMWarmup

            self.logger.info("Starting LLM warmup process...")
            warmup = LLMWarmup(self.config, self.arvis_core.llm_client)

            # Connect signals
            warmup.warmup_started.connect(lambda: self.status_panel.add_system_message("🔥 Прогрев LLM..."))
            warmup.warmup_progress.connect(self._handle_warmup_progress)
            warmup.warmup_completed.connect(self._handle_warmup_completed)
            warmup.warmup_failed.connect(self._handle_warmup_failed)

            # Start async warmup
            warmup.warmup_async()

        except Exception as e:
            self.logger.error(f"Failed to start LLM warmup: {e}")

    def _handle_warmup_progress(self, progress: int, message: str):
        """Handle warmup progress updates"""
        try:
            if progress % 20 == 0:  # Log every 20%
                self.logger.debug(f"LLM warmup: {progress}% - {message}")
        except Exception as e:
            self.logger.debug(f"Warmup progress handler error: {e}")

    def _handle_warmup_completed(self, duration: float):
        """Handle warmup completion"""
        try:
            self.logger.info(f"LLM warmup completed in {duration:.2f}s")
            self.status_panel.add_system_message(f"✅ LLM готов ({duration:.1f}с)")
        except Exception as e:
            self.logger.debug(f"Warmup completion handler error: {e}")

    def _handle_warmup_failed(self, error: str):
        """Handle warmup failure"""
        try:
            self.logger.warning(f"LLM warmup failed: {error}")
            self.status_panel.add_system_message(f"⚠️ Прогрев LLM не удался")
        except Exception as e:
            self.logger.debug(f"Warmup failure handler error: {e}")

    def start_ollama_if_needed(self):
        """Start Ollama server if autostart is enabled and it's not running"""
        try:
            from utils.ollama_manager import get_ollama_manager

            self.logger.info("Checking Ollama status...")
            self.ollama_manager = get_ollama_manager(self.config)

            # Check if Ollama is already running
            if self.ollama_manager.is_ollama_running():
                self.logger.info("Ollama is already running.")
                self.status_panel.add_system_message("🟢 Ollama: Запущен")
                return

            # Start Ollama
            if hasattr(self.config, "get_ollama_launch_mode"):
                launch_mode = self.config.get_ollama_launch_mode()
            else:
                launch_mode = str(
                    self.config.get(
                        "security.ollama.launch_mode",
                        self.config.get("startup.ollama_launch_mode", "background"),
                    )
                    or "background"
                ).lower()
            self.logger.info(f"Starting Ollama server (mode={launch_mode})...")
            self.status_panel.add_system_message(f"🟡 Ollama: запуск ({launch_mode})")

            # Start in background (non-blocking)
            from utils.async_manager import task_manager

            manager = self.ollama_manager
            if manager is None:
                raise RuntimeError("Ollama manager is not initialized")

            def start_task():
                success, message = manager.start_ollama(
                    wait_for_ready=True,
                    launch_mode=launch_mode,
                )
                return success, message

            def on_complete(task_id, result):
                success, message = result
                if success:
                    self.logger.info(f"Ollama started: {message}")
                    self.status_panel.add_system_message(f"🟢 Ollama готов")
                else:
                    self.logger.error(f"Ollama start failed: {message}")
                    self.status_panel.add_system_message(f"🔴 Ошибка Ollama")

            def on_error(task_id, error):
                self.logger.error(f"Ollama start error: {error}")
                fallback_hint = "Запустите 'ollama serve' в отдельном окне и повторите."
                self.status_panel.add_system_message(f"🔴 Ошибка Ollama: {error}. {fallback_hint}")

            def on_finally(task_id):
                self.logger.debug(f"Ollama startup task '{task_id}' finished")

            task_manager.run_async(
                task_id="ollama_startup",
                func=start_task,
                on_complete=on_complete,
                on_error=on_error,
                on_finally=on_finally,
            )

        except Exception as e:
            self.logger.error(f"Failed to start Ollama: {e}")
            self.status_panel.add_system_message("🔴 Ошибка Ollama")

    def init_arvis_core_delayed(self):
        """Initialize Arvis core with authentication (Phase 2 Day 4 + Enhanced Login)"""
        try:
            self.logger.info("Starting authentication flow...")

            # Проверяем настройки безопасности
            require_login = bool(self.config.get("security.auth.require_login", True))  # Changed default to True

            if require_login:
                # Показываем УЛУЧШЕННЫЙ диалог входа перед инициализацией core
                from PyQt6.QtWidgets import QDialog

                from .enhanced_login_dialog import EnhancedLoginDialog

                login_dialog = EnhancedLoginDialog(self)
                result = login_dialog.exec()

                if result == QDialog.Accepted:
                    # Пользователь вошёл успешно
                    user_id, username, role = login_dialog.get_credentials()
                    self.handle_login_success(user_id, username, role)
                else:
                    # Пользователь отменил вход - закрываем приложение
                    self.logger.info("Login cancelled by user, closing application")
                    self.close()
            else:
                # RBAC выключен - запускаем без аутентификации
                self.logger.info("Authentication disabled, starting without login")
                self.init_arvis_core()
                # Прогреваем LLM даже без авторизации
                QTimer.singleShot(2000, self.warmup_llm)

        except Exception as e:
            self.logger.error(f"Authentication flow failed: {e}")
            # Fallback: гостевой режим
            self.handle_login_success(None, "Guest", "guest")

    def connect_signals(self):
        """Connect UI signals"""
        # Chat panel signals
        self.chat_panel.message_sent.connect(self.handle_user_message_async)
        self.chat_panel.microphone_clicked.connect(self.handle_microphone_async)
        self.chat_panel.clear_chat_requested.connect(self.clear_chat)
        self.chat_panel.cancel_request.connect(self.cancel_current_request)
        self.chat_panel.orb_toggle_requested.connect(self.handle_orb_toggle)
        self.chat_panel.settings_clicked.connect(self.show_settings)  # Настройки теперь в ChatPanel
        self.chat_panel.history_clicked.connect(self.show_chat_history)  # История разговоров
        self.chat_panel.user_management_clicked.connect(self.show_user_management)  # Управление пользователями

        # Сигналы обратной связи от кнопок
        self.chat_panel.message_liked.connect(self.handle_message_liked)
        self.chat_panel.message_disliked.connect(self.handle_message_disliked)
        self.chat_panel.message_retry_requested.connect(self.handle_message_retry)
        self.chat_panel.message_voice_over_requested.connect(self.handle_message_voice_over)

        # Status panel signals (Phase 2 Day 4)
        self.status_panel.logout_requested.connect(self.handle_logout)

    def handle_login_success(self, user_id: Optional[str], username: Optional[str], role: Optional[str] = None):
        """Handle successful login and initialize core (Phase 2 Day 4 + Enhanced)"""
        try:
            name_for_log = username or "Unknown"
            self.logger.info(f"User logged in: {name_for_log} (ID: {user_id}, Role: {role})")

            # Сохраняем user_id для использования в настройках и других диалогах
            self.current_user_id = user_id

            # Получаем менеджеры безопасности
            from utils.security import Role, get_auth_manager, get_rbac_manager

            auth = get_auth_manager()
            rbac = get_rbac_manager()

            user_obj = None
            storage = getattr(auth, "storage", None)
            if storage and user_id:
                try:
                    user_obj = storage.get_user_by_id(user_id)
                except Exception as fetch_error:
                    self.logger.warning(f"Failed to load user by id: {fetch_error}")

            # Fallback: try to fetch by username if ID not found
            if storage and not user_obj and username:
                try:
                    user_obj = storage.get_user(username)
                except Exception as fetch_error:
                    self.logger.debug(f"Fallback user lookup failed: {fetch_error}")

            if user_obj:
                username = user_obj.username or username

            subscription_tier = self._resolve_subscription_tier(username if user_obj else None, user_id)
            subscription_display = self._resolve_subscription_title(subscription_tier)
            subscription_role = self._resolve_role_for_subscription(subscription_tier)

            default_role_key = str(self.config.get("security.rbac.default_role", "user") or "user")
            default_role = Role.__members__.get(default_role_key.upper(), Role.USER)

            resolved_role = default_role
            if user_obj and user_obj.role:
                resolved_role = user_obj.role

            enforce_subscriptions = bool(self.config.get("security.rbac.enforce_subscriptions", True))
            if subscription_role and (enforce_subscriptions or not user_obj):
                resolved_role = subscription_role

            if not user_id:
                resolved_role = subscription_role or Role.GUEST
                self.logger.info("Guest mode activated")

            role_name = resolved_role.value
            rbac.set_current_user(user_id)
            rbac.set_role(resolved_role)
            self.logger.info(f"Active role: {role_name}, subscription: {subscription_tier or 'n/a'}")

            # Обновляем UI индикатор пользователя
            username_display = username or "User"
            self.status_panel.set_user_info(username_display, role_name, user_id, subscription_display)
            
            # ✅ ИСПРАВЛЕНИЕ: Обновляем видимость кнопки управления пользователями при смене аккаунта
            is_admin = resolved_role == Role.ADMIN
            self.chat_panel.set_user_management_visible(is_admin)
            self.logger.info(f"User management button visibility: {is_admin} (role: {role_name})")

            # Сохраняем токен удалённой авторизации/URL сервера для диалога смены пароля
            try:
                from utils.security.remote_auth_client import RemoteAuthClient
                client = RemoteAuthClient.get()
                if client and client.is_authenticated():
                    self.access_token = client.access_token
                    from config.config import Config as _Cfg
                    self.auth_server_url = _Cfg().get_auth_server_url()
            except Exception:
                pass

            # Инициализируем ArvisCore с текущим пользователем
            self.init_arvis_core()

            # Передаём user_id в ArvisCore для модулей
            if self.arvis_core and user_id:
                self.arvis_core.set_current_user(user_id)

            # ПРОГРЕВАЕМ LLM после успешного логина для быстрого первого ответа
            self.logger.info("Starting LLM warmup after login...")
            QTimer.singleShot(1500, self.warmup_llm)  # Запускаем через 1.5 сек после инициализации core

        except Exception as e:
            self.logger.error(f"Login success handler failed: {e}")
            # Продолжаем работу в гостевом режиме
            fallback_subscription = self._resolve_subscription_title(self._resolve_subscription_tier(None, None))
            self.status_panel.set_user_info("Guest", "guest", None, fallback_subscription)
            self.init_arvis_core()

    def handle_logout(self):
        """Handle user logout request (Phase 2 Day 4)"""
        try:
            self.logger.info("Logout requested")

            # Очищаем текущего пользователя из RBAC
            from utils.security import Role, get_rbac_manager

            rbac = get_rbac_manager()
            rbac.set_current_user(None)
            rbac.set_role(Role.GUEST)

            # Очищаем user_id в ArvisCore
            if self.arvis_core:
                self.arvis_core.set_current_user(None)

            # Показываем УЛУЧШЕННЫЙ диалог входа снова
            from PyQt6.QtWidgets import QDialog

            from .enhanced_login_dialog import EnhancedLoginDialog

            login_dialog = EnhancedLoginDialog(self)
            result = login_dialog.exec()

            if result == QDialog.Accepted:
                user_id, username, role = login_dialog.get_credentials()
                self.handle_login_success(user_id, username, role)
            else:
                # Пользователь отменил повторный вход - закрываем приложение
                self.logger.info("Re-login cancelled, closing application")
                self.close()

        except Exception as e:
            self.logger.error(f"Logout handler failed: {e}")

    def _resolve_subscription_tier(self, username: Optional[str], user_id: Optional[str]) -> Optional[str]:
        """Определить тарифную подписку пользователя по настройкам безопасности"""
        try:
            subscriptions_enabled = bool(self.config.get("security.subscriptions.enabled", False))
            if not subscriptions_enabled:
                return None

            # Проверяем назначение по user_id
            if user_id:
                user_id_assignments = self.config.get("security.subscriptions.user_id_assignments", {}) or {}
                if isinstance(user_id_assignments, dict):
                    tier = user_id_assignments.get(user_id)
                else:
                    tier = None
                if isinstance(tier, str) and tier:
                    return tier

            # Проверяем назначение по username
            if username:
                assignments = self.config.get("security.subscriptions.user_assignments", {}) or {}
                if isinstance(assignments, dict):
                    tier = assignments.get(username)
                else:
                    tier = None
                if isinstance(tier, str) and tier:
                    return tier

            # Гостевой и значения по умолчанию
            guest_tier_value = self.config.get("security.subscriptions.guest_tier", None)
            guest_tier = guest_tier_value if isinstance(guest_tier_value, str) and guest_tier_value else None
            default_tier_value = self.config.get("security.subscriptions.default_tier", None)
            default_tier = default_tier_value if isinstance(default_tier_value, str) and default_tier_value else None

            if not user_id:
                return guest_tier or default_tier

            return default_tier
        except Exception as e:
            self.logger.debug(f"Failed to resolve subscription tier: {e}")
            return None

    def _resolve_subscription_title(self, tier: Optional[str]) -> Optional[str]:
        if not tier:
            return None
        try:
            display_name = self.config.get(f"security.subscriptions.tiers.{tier}.title", None)
            if isinstance(display_name, str) and display_name:
                return display_name
        except Exception:
            pass
        return tier.capitalize() if tier else None

    def _resolve_role_for_subscription(self, tier: Optional[str]):
        if not tier:
            return None
        try:
            from utils.security import Role

            role_key = self.config.get(f"security.subscriptions.tiers.{tier}.role", None)
            if not role_key:
                return None
            role = Role.__members__.get(str(role_key).upper())
            return role
        except Exception as e:
            self.logger.debug(f"Failed to resolve role for tier '{tier}': {e}")
            return None

    def handle_message_liked(self, message: str):
        """Обработчик кнопки 'Хороший ответ'"""
        self.logger.info(f"Пользователь отметил сообщение как хорошее: {message[:50]}...")
        saved = False
        if self.arvis_core:
            saved = self.arvis_core.set_assistant_feedback(message, "positive")
        status_text = _("✓ Отзыв принят: Хороший ответ") if saved else _("⚠️ Не удалось сохранить оценку.")
        self.status_panel.add_system_message(status_text)

    def handle_message_disliked(self, message: str):
        """Обработчик кнопки 'Плохой ответ'"""
        self.logger.info(f"Пользователь отметил сообщение как плохое: {message[:50]}...")
        saved = False
        if self.arvis_core:
            saved = self.arvis_core.set_assistant_feedback(message, "negative")
        status_text = _("✗ Отзыв принят: Плохой ответ") if saved else _("⚠️ Не удалось сохранить оценку.")
        self.status_panel.add_system_message(status_text)

    def handle_message_retry(self, message: str):
        """Обработчик кнопки 'Попробовать ещё раз'

        Использует новый метод regenerate_last_response() для корректной регенерации
        без создания дубликатов пользовательских сообщений.
        """
        self.logger.info(f"Пользователь запросил повтор для сообщения: {message[:50]}...")

        if not self.arvis_core:
            self.logger.error("Arvis core not initialized")
            self.status_panel.add_system_message("❌ Ядро не инициализировано", 3000)
            return

        # Используем новый метод regenerate_last_response вместо прямого process_message
        self.chat_panel.add_system_message("🔄 Генерирую новый ответ...")

        success = self.arvis_core.regenerate_last_response()
        if not success:
            self.status_panel.add_system_message("⚠️ Не удалось запустить регенерацию", 3000)

    def handle_message_voice_over(self, message: str):
        """Обработчик кнопки 'Озвучить'"""
        self.logger.info(f"Пользователь запросил озвучку сообщения: {message[:50]}...")
        if self.arvis_core and self.arvis_core.tts_engine:
            try:
                # Проверяем готовность TTS
                if not self.arvis_core.tts_engine.is_ready():
                    self.logger.error("TTS engine не готов")
                    self.status_panel.add_system_message("❌ TTS не готов", 3000)
                    return

                # Проверяем настройки TTS
                if not self.arvis_core.tts_engine.tts_enabled:
                    self.logger.info("TTS отключен в настройках, включаем временно")
                    self.arvis_core.tts_engine.tts_enabled = True

                self.logger.info("Начинаем озвучивание через TTS engine")
                # Озвучиваем сообщение через TTS
                self.arvis_core.tts_engine.speak(message)
                self.status_panel.add_system_message("🔊 Озвучиваю сообщение...", 2000)
            except RuntimeError as re:
                self.logger.error(f"RuntimeError при озвучивании: {re}")
                self.status_panel.add_system_message(f"❌ RuntimeError: {str(re)[:50]}...", 4000)
                # Попробуем еще раз после небольшой задержки
                QTimer.singleShot(100, lambda: self._retry_voice_over(message))
            except Exception as e:
                self.logger.error(f"Ошибка при озвучивании: {e}")
                self.status_panel.add_system_message(f"❌ Ошибка озвучивания: {str(e)[:50]}...", 4000)
        else:
            if not self.arvis_core:
                self.logger.error("Arvis core не инициализирован")
                self.status_panel.add_system_message("❌ Arvis core не готов", 3000)
            elif not self.arvis_core.tts_engine:
                self.logger.error("TTS engine не инициализирован")
                self.status_panel.add_system_message("❌ TTS engine не инициализирован", 3000)
            else:
                self.logger.error("TTS engine not available")
                self.status_panel.add_system_message("❌ TTS недоступен", 3000)

    # Удалено: кнопка «Озвучить последний ответ»

    def _retry_voice_over(self, message: str):
        """Повторная попытка озвучки после ошибки"""
        try:
            if self.arvis_core and self.arvis_core.tts_engine:
                self.logger.info("Выполняем повторную попытку озвучивания")
                self.arvis_core.tts_engine.speak(message)
                self.logger.info("Повторная попытка озвучки успешна")
                self.status_panel.add_system_message("✓ Повторная попытка озвучки успешна", 2000)
        except Exception as e:
            self.logger.error(f"Повторная попытка озвучки также неудачна: {e}")
            self.status_panel.add_system_message(f"❌ Повторная попытка неудачна: {str(e)[:50]}...", 4000)

    def clear_chat(self):
        """Clear chat history"""
        self.chat_panel.clear_chat()
        if self.arvis_core:
            self.arvis_core.clear_conversation_history()
        self.logger.info("Chat cleared")

    def set_user_role(self, role_str: str):
        """Установить роль пользователя и адаптировать UI"""
        try:
            from utils.security import Role

            # Показываем кнопку управления пользователями только для администраторов
            is_admin = role_str == Role.ADMIN.value
            self.chat_panel.set_user_management_visible(is_admin)

        except Exception as e:
            self.logger.error(f"Failed to set user role: {e}")

    def show_user_management(self):
        """Показать панель управления пользователями (только для админов)"""
        try:
            from i18n.i18n import apply_to_widget_tree
            from src.gui.user_management_panel import UserManagementPanel

            # Проверяем права администратора
            from utils.security import Permission, Role, get_rbac_manager

            rbac = get_rbac_manager()

            if not self.current_user_id:
                from PyQt6.QtWidgets import QMessageBox

                QMessageBox.warning(self, _("Ошибка доступа"), _("Необходимо войти в систему"))
                return

            # ✅ ИСПРАВЛЕНИЕ: Используем правильную проверку прав через текущую роль
            current_role = rbac.get_role()
            if current_role != Role.ADMIN:
                from PyQt6.QtWidgets import QMessageBox

                self.logger.warning(f"Access denied: user role is {current_role.value}, required ADMIN")
                QMessageBox.warning(self, _("Ошибка доступа"), _("У вас нет прав для управления пользователями"))
                return

            # Показываем панель
            panel = UserManagementPanel(self)

            try:
                apply_to_widget_tree(panel)
            except Exception:
                pass

            panel.exec()

        except Exception as e:
            self.logger.error(f"Failed to show user management panel: {e}")
            from PyQt6.QtWidgets import QMessageBox

            QMessageBox.critical(
                self, _("Ошибка"), _("Не удалось открыть панель управления:\n{error}").format(error=str(e))
            )

    def show_settings(self):
        """Показать диалог настроек"""
        if not self.settings_dialog:
            self.settings_dialog = SettingsDialog(self.config, self)
        # Устанавливаем current_user_id перед открытием
        try:
            self.settings_dialog.set_current_user(self.current_user_id)
        except Exception:
            self.settings_dialog.current_user_id = self.current_user_id
        # Применяем текущий перевод к диалогу перед показом
        try:
            apply_to_widget_tree(self.settings_dialog)
        except Exception:
            pass
        result = self.settings_dialog.exec()
        if result == self.settings_dialog.Accepted:
            # Update TTS settings without full restart
            self.update_tts_settings()
            # Reload configuration and restart core if needed for other changes
            self.restart_arvis_core()

    def show_chat_history(self):
        """Show chat history dialog"""
        try:
            if not self.arvis_core or not hasattr(self.arvis_core, "conversation_history_manager"):
                self.logger.error("Conversation history manager not available")
                from PyQt6.QtWidgets import QMessageBox

                QMessageBox.warning(
                    self,
                    _("История недоступна"),
                    _("Система истории разговоров ещё не инициализирована.\nПожалуйста, подождите."),
                )
                return

            # Создаём новый диалог каждый раз для актуальности данных
            history_dialog = ChatHistoryDialog(self.arvis_core.conversation_history_manager, self)

            try:
                apply_to_widget_tree(history_dialog)
            except Exception:
                pass

            # Подключаем сигнал очистки истории
            history_dialog.history_cleared.connect(self.on_history_cleared)

            # Скрываем орб на время просмотра истории
            orb_was_visible = False
            if hasattr(self.status_panel, "orb_widget"):
                orb_was_visible = self.status_panel.orb_widget.isVisible()
                if orb_was_visible:
                    self.status_panel.orb_widget.hide()

            # Показываем диалог модально
            history_dialog.exec()

            # Восстанавливаем орб после закрытия
            if orb_was_visible and hasattr(self.status_panel, "orb_widget"):
                self.status_panel.orb_widget.show()

            self.logger.info("Chat history dialog closed")

        except Exception as e:
            self.logger.error(f"Error showing chat history: {e}")
            from PyQt6.QtWidgets import QMessageBox

            QMessageBox.critical(self, _("Ошибка"), _("Не удалось открыть историю:\n{error}").format(error=e))

    def on_history_cleared(self):
        """Handle history cleared signal from history dialog"""
        try:
            # Очищаем текущий чат в UI
            self.chat_panel.clear_chat()
            self.logger.info("Chat cleared after history was cleared")
        except Exception as e:
            self.logger.error(f"Error clearing chat after history clear: {e}")
            # Обновляем язык интерфейса согласно новым настройкам
            try:
                new_ui_lang = str(self.config.get("language.ui", "ru") or "ru")
                I18N.get().set_language(new_ui_lang)
            except Exception:
                pass
            # Если был сменён язык — применим перевод к главному окну
            try:
                apply_to_widget_tree(self)
            except Exception:
                pass

    def restart_application(self):
        """Restart the application"""
        self.logger.info("Restarting application...")
        # Clean shutdown
        if self.arvis_core:
            self.arvis_core.shutdown()

        # Restart
        from PyQt6.QtWidgets import QApplication

        QApplication.quit()

        import os
        import sys

        os.execl(sys.executable, sys.executable, *sys.argv)

    def restart_arvis_core(self):
        """Restart Arvis core with new configuration"""
        try:
            if self.arvis_core:
                self.arvis_core.shutdown()

            self.arvis_core = ArvisCore(self.config)
            self.chat_panel.set_arvis_core(self.arvis_core)
            self.status_panel.set_arvis_core(self.arvis_core)

            self.logger.info("Arvis core restarted successfully")

        except Exception as e:
            self.logger.error(f"Failed to restart Arvis core: {e}")

    def update_tts_settings(self):
        """Update TTS settings without full restart"""
        try:
            if self.arvis_core and self.arvis_core.tts_engine:
                # Update TTS mode and enabled state
                tts_mode = self.config.get("tts.mode", "realtime")
                tts_enabled = self.config.get("tts.enabled", True)

                self.arvis_core.tts_engine.set_mode(tts_mode)
                self.arvis_core.tts_engine.set_enabled(tts_enabled)

                self.logger.info(f"TTS settings updated: mode={tts_mode}, enabled={tts_enabled}")

        except Exception as e:
            self.logger.error(f"Failed to update TTS settings: {e}")

    def _handle_status_changed(self, status: dict):
        """Handle core status changes to update quick UI indicators (e.g., mic)."""
        try:
            if status and isinstance(status, dict) and "is_recording" in status:
                self.chat_panel.set_recording_active(bool(status["is_recording"]))
            if status and isinstance(status, dict) and status.get("stt_model_ready"):
                self._show_stt_ready_popup(status.get("stt_model_path"))
        except Exception:
            pass

    def _on_stt_model_ready(self, model_path: str):
        """Direct handler for STT readiness signal."""
        self._show_stt_ready_popup(model_path)
        try:
            self.stt_ready.emit(model_path or "")
        except Exception:
            pass

    def _on_voice_assets_ready(self):
        """Relay voice asset readiness to the shell and optionally notify UI."""
        try:
            self.voice_assets_ready.emit()
        except Exception:
            pass

        try:
            self.status_panel.add_system_message("🔊 Фразы активации сгенерированы", 4000)
        except Exception:
            self.logger.debug("Failed to push voice asset notification to status panel")

    def _show_stt_ready_popup(self, model_path: str | None):
        """Show floating notification once when Vosk models are ready."""
        if self._stt_popup_shown or not self.floating_notification:
            return

        try:
            model_name = Path(model_path).name if model_path else "Vosk"
        except Exception:
            model_name = "Vosk"

        message = f"🎧 Модели Vosk ({model_name}) готовы к работе"

        try:
            self.floating_notification.reposition()
            self.floating_notification.show_message(message, duration_ms=7000)
            self._stt_popup_shown = True
        except Exception as exc:
            self.logger.debug(f"Failed to show STT ready popup: {exc}")

    def cancel_current_request(self):
        """Cancel current LLM request"""
        if self.arvis_core:
            self.arvis_core.cancel_current_request()
        self.logger.info("User requested to cancel current request")

    # Метод toggle_play_pause удален - управление аудио перенесено в ChatPanel

    def handle_orb_toggle(self):
        """Handle orb toggle button click from ChatPanel"""
        # Передаем управление в StatusPanel
        self.status_panel.toggle_orb_visibility()
        self.logger.info("Orb visibility toggled from ChatPanel")

    def apply_styles(self):
        """Apply custom styles to main window"""
        self.setStyleSheet(
            """
            QMainWindow {
                background-color: rgb(43, 43, 43);
            }

            QSplitter::handle {
                background-color: rgb(60, 60, 60);
            }

            QSplitter::handle:horizontal {
                width: 2px;
            }

            QSplitter::handle:vertical {
                height: 2px;
            }
        """
        )

    def handle_user_message_async(self, message: str):
        """Handle user message asynchronously to prevent UI blocking"""
        # Немедленно отвечаем UI, чтобы кнопка не зависала
        QTimer.singleShot(10, lambda: self.handle_user_message(message))

    def handle_microphone_async(self):
        """Handle microphone click asynchronously"""
        # Немедленно отвечаем UI, чтобы кнопка не зависала
        QTimer.singleShot(10, self.handle_microphone)

    def handle_user_message(self, message: str):
        """Handle user message"""
        if self.arvis_core:
            self.arvis_core.process_message(message)
        self.logger.info(f"User message: {message}")

    def handle_microphone(self):
        """Handle microphone button click"""
        if self.arvis_core:
            self.arvis_core.toggle_voice_recording()
        self.logger.info("Microphone toggled")

    def closeEvent(self, event):
        """Handle application close event"""
        self.logger.info("Shutting down Arvis...")

        if self.arvis_core:
            self.arvis_core.shutdown()

        # Cleanup Ollama if we started it
        if self.ollama_manager:
            try:
                self.ollama_manager.cleanup()
            except Exception as e:
                self.logger.error(f"Ollama cleanup error: {e}")

        event.accept()

    def resizeEvent(self, event):
        """Ensure floating notifications stay anchored after resize."""
        super().resizeEvent(event)
        try:
            if self.floating_notification and self.floating_notification.isVisible():
                self.floating_notification.reposition()
        except Exception:
            pass

    def check_for_updates_background(self):
        """Проверить обновления в фоновом режиме"""
        try:
            if self.update_check_thread and self.update_check_thread.isRunning():
                return

            self.logger.info("Запуск фоновой проверки обновлений...")
            self.update_check_thread = UpdateCheckThread(self.update_checker)
            self.update_check_thread.update_available.connect(self.show_update_notification)
            self.update_check_thread.check_completed.connect(lambda ok: self.logger.debug("Проверка обновлений завершена"))
            self.update_check_thread.start()
        except Exception as e:
            self.logger.error(f"Ошибка запуска проверки обновлений: {e}")

    def check_for_updates_manual(self):
        """Ручная проверка обновлений (из меню)"""
        try:
            if self.update_check_thread and self.update_check_thread.isRunning():
                self.show_notification(_("Проверка обновлений уже выполняется..."), "info")
                return

            self.show_notification(_("Проверка обновлений..."), "info")
            self.update_check_thread = UpdateCheckThread(self.update_checker)
            self.update_check_thread.update_available.connect(self.show_update_notification)
            self.update_check_thread.check_completed.connect(
                lambda ok: (self.status_panel.add_system_message("✓ Обновлений не найдено") if not ok else None)
            )
            self.update_check_thread.start()
        except Exception as e:
            self.logger.error(f"Ошибка ручной проверки обновлений: {e}")
            self.show_notification(_("Ошибка проверки обновлений"), "error")

    def show_update_notification(self, update_info: dict):
        """Показать уведомление о доступном обновлении"""
        try:
            dialog = UpdateNotificationDialog(update_info, self.update_checker, self)
            dialog.exec()
        except Exception as e:
            self.logger.error(f"Ошибка отображения диалога обновления: {e}")
