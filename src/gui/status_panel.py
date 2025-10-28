"""
Status panel for Arvis application
"""

import math
from pathlib import Path
from typing import Optional, Any

from PyQt6.QtCore import QEasingCurve, QPropertyAnimation, QRect, QRectF, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QBrush, QColor, QFont, QPainter, QPen
from PyQt6.QtSvgWidgets import QSvgWidget
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QProgressBar, QPushButton, QTextEdit, QVBoxLayout, QWidget

from i18n import _


class ArvisOrb(QSvgWidget):
    """Animated Arvis orb widget for status display"""

    def __init__(self, parent=None):
        super().__init__(parent)
        # Increase orb size and ensure transparent background (no visible square)
        self.setFixedSize(180, 180)
        self.setStyleSheet("background: transparent; border: none;")
        self.current_state = "norm"
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self.animate_pulse)
        self.pulse_value = 0
        self.load_orb()

    def load_orb(self, state="norm"):
        """Load orb SVG based on state"""
        orb_files = {
            "norm": "UXUI/Orb/Orb_norm.svg",
            "thinking": "UXUI/Orb/Orb_thinkin.svg",
            "error": "UXUI/Orb/Orb_error.svg",
            "recording": "UXUI/Orb/Orb_thinkin.svg",  # Используем thinking орб для записи
        }

        orb_path = Path(orb_files.get(state, orb_files["norm"]))
        if orb_path.exists():
            self.load(str(orb_path))
        else:
            # Create fallback visual
            self.create_fallback_orb(state)

    def create_fallback_orb(self, state):
        """Create fallback orb visual when SVG not available"""
        colors = {
            "norm": "#4a9eff",
            "thinking": "#ff9a4a",
            "error": "#ff4a4a",
            "recording": "#ff4a9a",  # Розовый для записи
        }

        color = colors.get(state, colors["norm"])
        self.setStyleSheet(
            f"""
            QSvgWidget {{
                background: qradialgradient(cx: 0.5, cy: 0.5, radius: 0.5,
                                          fx: 0.3, fy: 0.3,
                                          stop: 0 {color},
                                          stop: 1 {color}AA);
                border-radius: 75px;
                border: 3px solid rgba(255, 255, 255, 0.2);
            }}
        """
        )

    def set_state(self, state: str):
        """Set orb state (norm, thinking, error, recording)"""
        if self.current_state != state:
            self.current_state = state
            self.load_orb(state)

            if state in ["thinking", "recording"]:
                self.start_thinking_animation()
            else:
                self.stop_thinking_animation()

    def start_thinking_animation(self):
        """Start thinking animation"""
        # Временно отключаем анимацию для диагностики
        # self.animation_timer.start(100)  # 100ms updates
        pass

    def stop_thinking_animation(self):
        """Stop thinking animation"""
        self.animation_timer.stop()
        self.pulse_value = 0

    def animate_pulse(self):
        """Animate pulsing effect"""
        self.pulse_value += 0.1
        if self.pulse_value >= 2 * math.pi:
            self.pulse_value = 0
        self.update()

    def paintEvent(self, event):
        """Custom paint event for animations"""
        try:
            # Временно отключаем кастомную отрисовку для диагностики
            super().paintEvent(event)

            # Убираем анимацию pulsing ring
            # if self.current_state == "thinking" and hasattr(self, 'pulse_value'):
            #     painter = QPainter(self)
            #     painter.setRenderHint(QPainter.Antialiasing)
            #
            #     # Draw pulsing ring
            #     # Align to the visual center of the SVG; compensate possible viewBox padding
            #     r = self.rect()
            #     center = r.center()
            #     # Slight vertical offset to better align with orb visual center
            #     center.setY(center.y() + 1)
            #     radius = 70 + 10 * math.sin(self.pulse_value)
            #
            #     pen = QPen(QColor(255, 154, 74, 100))
            #     pen.setWidth(3)
            #     painter.setPen(pen)
            #     painter.setBrush(Qt.NoBrush)
            #
            #     painter.drawEllipse(center, int(radius), int(radius))
        except Exception as e:
            # Логируем ошибку, но не прерываем работу
            print(f"Paint event error: {e}")


class SvgButton(QPushButton):
    """Custom button with SVG icons for status panel"""

    def __init__(self, svg_normal: str, svg_active: Optional[str] = None, size=(50, 50), parent=None):
        super().__init__(parent)
        self.svg_normal = svg_normal
        self.svg_active = svg_active or svg_normal
        self.setFixedSize(*size)
        # Убираем фокусную рамку
        try:
            self.setFocusPolicy(Qt.NoFocus)  # type: ignore[attr-defined]
        except Exception:
            pass
        self.setup_style()

    def setup_style(self):
        """Setup button style"""
        self.setStyleSheet(
            """
            QPushButton {
                border: none;
                background: transparent;
                border-radius: 25px;
            }
            /* Убрали подсветку при наведении */
            QPushButton:hover {
                background-color: transparent;
            }
            QPushButton:pressed {
                background-color: rgba(255, 255, 255, 0.25);
            }
        """
        )

    def paintEvent(self, event):
        """Custom paint event to draw SVG"""
        super().paintEvent(event)

        painter = QPainter(self)
        try:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        except Exception:
            # Fallback for environments where enum location differs
            try:
                painter.setRenderHint(QPainter.Antialiasing)  # type: ignore[attr-defined]
            except Exception:
                pass

        # Choose SVG based on state
        svg_path = Path(self.svg_active if self.isDown() or self.underMouse() else self.svg_normal)

        if svg_path.exists():
            from PyQt6.QtSvg import QSvgRenderer

            renderer = QSvgRenderer(str(svg_path))
            rect = self.rect().adjusted(8, 8, -8, -8)
            renderer.render(painter, QRectF(rect))


class StatusPanel(QWidget):
    """Status and control panel widget"""

    # Сигналы
    logout_requested = pyqtSignal()  # Emitted when user requests logout

    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config
        self.arvis_core = None
        self.orb_visible = False  # Орб скрыт по умолчанию
        self.orb_animation_in_progress = False  # Защита от множественных вызовов
        self._animation_connected = False  # Флаг подключения анимации
        self._stt_notification_shown = False
        self._chat_panel: Optional[Any] = None  # ChatPanel reference for forwarding system messages

        # User info
        self.current_user_id = None
        self.current_username = None
        self.current_role = None

        from utils.logger import ModuleLogger

        self.logger = ModuleLogger("StatusPanel")

        self.init_ui()

    def init_ui(self):
        """Initialize status panel UI"""
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(20)

        # Заголовок с названием и версией убран
        # Кнопка управления орбом перенесена в ChatPanel

        # User indicator (moved to Settings dialog by design)
        # Keep widget for compatibility but do not add to layout
        try:
            self.user_indicator = self._create_user_indicator()
            # Do not add to layout to avoid stretching when orb is hidden
        except Exception:
            self.user_indicator = None

        # Arvis orb (central status display) - initially hidden
        self.orb_frame = QFrame()
        self.orb_frame.setStyleSheet(
            """
            QFrame {
                background: transparent;
                border: none;
            }
        """
        )

        # Создаем горизонтальный контейнер для центрирования по горизонтали
        horizontal_container = QHBoxLayout()
        horizontal_container.addStretch()  # Левый отступ

        # Создаем вертикальный контейнер для центрирования по вертикали
        orb_layout = QVBoxLayout()
        orb_layout.setContentsMargins(20, 20, 20, 20)
        orb_layout.addStretch()  # Верхний отступ

        self.orb = ArvisOrb()  # Переименуем для консистентности
        orb_layout.addWidget(self.orb)

        orb_layout.addStretch()  # Нижний отступ

        # Создаем виджет-контейнер для вертикального макета
        vertical_widget = QWidget()
        vertical_widget.setLayout(orb_layout)

        # Добавляем в горизонтальный макет
        horizontal_container.addWidget(vertical_widget)
        horizontal_container.addStretch()  # Правый отступ

        # Recording indicator
        self.recording_label = QLabel("🎤 Запись...")
        self.recording_label.setStyleSheet(
            """
            QLabel {
                color: #ff4a9a;
                font-size: 14px;
                font-weight: bold;
                padding: 5px 10px;
                background-color: rgba(255, 74, 154, 0.1);
                border-radius: 10px;
                border: 1px solid rgba(255, 74, 154, 0.3);
            }
        """
        )
        # self.recording_label.setAlignment(Qt.AlignmentFlag.AlignHCenter) # Убрано из-за проблем с Qt
        self.recording_label.hide()  # Скрыт по умолчанию
        orb_layout.addWidget(self.recording_label)

        # Создаем и устанавливаем горизонтальный макет в орб фрейм
        main_layout = QHBoxLayout()
        main_layout.addLayout(horizontal_container)
        self.orb_frame.setLayout(main_layout)

        # Status label
        # Remove readiness label below orb to declutter
        self.status_label = QLabel("")
        self.status_label.hide()

        self.orb_frame.hide()  # Орб скрыт по умолчанию

        # Initialize animation for orb - TV turn-on effect
        self.orb_animation = QPropertyAnimation(self.orb_frame, b"maximumHeight")
        self.orb_animation.setDuration(800)  # Медленнее для эффекта телевизора
        self.orb_animation.setEasingCurve(QEasingCurve.Type.OutElastic)  # Эластичный эффект как у старого ТВ

        # Дополнительная анимация для горизонтального расширения
        self.orb_width_animation = QPropertyAnimation(self.orb_frame, b"maximumWidth")
        self.orb_width_animation.setDuration(600)
        self.orb_width_animation.setEasingCurve(QEasingCurve.Type.OutQuad)

        # Кнопки управления аудио перенесены в ChatPanel

        # Блок системной информации убран

        # Кнопка настроек перенесена в ChatPanel

        # Notification area (removed from layout to declutter main UI)
        self.notifications_frame = QFrame()
        self.notifications_frame.setStyleSheet(
            """
            QFrame {
                background-color: rgba(255, 255, 255, 0.05);
                border-radius: 8px;
                border: 1px solid rgba(255, 255, 255, 0.1);
            }
        """
        )
        self.notifications_frame.hide()  # Hidden and not added to layout

        self.notifications_layout = QVBoxLayout()
        self.notifications_layout.setContentsMargins(10, 8, 10, 8)
        self.notifications_frame.setLayout(self.notifications_layout)

        # Add all components to main layout - минимальная компоновка
        layout.addWidget(self.orb_frame, 1)  # Орб (скрыт по умолчанию, управляется из ChatPanel)
    # Notifications are not added to layout by design

        self.setLayout(layout)

    def set_arvis_core(self, arvis_core):
        """Set Arvis core instance"""
        self.arvis_core = arvis_core
        if arvis_core:
            # Connect to core signals
            arvis_core.status_changed.connect(self.update_status)
            arvis_core.processing_started.connect(lambda: self.set_orb_state("thinking"))
            arvis_core.processing_finished.connect(lambda: self.set_orb_state("norm"))
            arvis_core.error_occurred.connect(lambda: self.set_orb_state("error"))

    def set_orb_state(self, state: str):
        """Set orb visual state"""
        self.orb.set_state(state)
        # Keep status internal without showing text under the orb

    def update_status(self, status_data: dict):
        """Update status information - only orb state now"""
        # Обновляем только состояние орба и индикатор записи
        if "is_recording" in status_data:
            if status_data["is_recording"]:
                self.orb.set_state("recording")
                self.recording_label.show()
            else:
                self.recording_label.hide()

        if "is_processing" in status_data and status_data["is_processing"]:
            if not ("is_recording" in status_data and status_data["is_recording"]):
                self.orb.set_state("thinking")
        elif not ("is_recording" in status_data and status_data["is_recording"]):
            self.orb.set_state("norm")

        if status_data.get("stt_model_ready") and not self._stt_notification_shown:
            model_path = status_data.get("stt_model_path")
            if model_path:
                try:
                    model_name = Path(model_path).name
                except Exception:
                    model_name = model_path
            else:
                model_name = "Vosk"
            self.add_system_message(f"🎧 Модель распознавания речи {model_name} загружена")
            self._stt_notification_shown = True

    def toggle_orb_visibility(self):
        """Toggle orb visibility with old TV turn-on animation"""
        # Защита от множественных быстрых нажатий
        if self.orb_animation_in_progress:
            return

        self.orb_animation_in_progress = True
        self.orb_visible = not self.orb_visible

        # Отключаем предыдущие соединения безопасно
        if hasattr(self, "_animation_connected") and self._animation_connected:
            try:
                self.orb_animation.finished.disconnect()
                if hasattr(self, "orb_width_animation"):
                    self.orb_width_animation.finished.disconnect()
                self._animation_connected = False
            except TypeError:
                # Соединения уже отключены - это нормально
                self._animation_connected = False

        if self.orb_visible:
            # Show orb with TV turn-on animation
            self.orb_frame.show()
            # Сначала устанавливаем размеры как у старого телевизора
            self.orb_frame.setMaximumHeight(2)  # Тонкая горизонтальная линия
            self.orb_frame.setMaximumWidth(50)  # Узкая полоска

            # Анимация высоты (вертикальное расширение)
            self.orb_animation.setStartValue(2)
            self.orb_animation.setEndValue(250)  # Полная высота орба

            # Анимация ширины с задержкой
            QTimer.singleShot(200, lambda: self._start_width_animation())

            def on_show_finished():
                self.orb_frame.setMaximumHeight(16777215)  # Reset to unlimited
                self.orb_frame.setMaximumWidth(16777215)  # Reset to unlimited
                self.orb_animation_in_progress = False  # Сбрасываем защиту

            self.orb_animation.finished.connect(on_show_finished)
            self._animation_connected = True

        else:
            # Hide orb with reverse TV animation
            current_height = self.orb_frame.height()
            current_width = self.orb_frame.width()

            # Сначала сжимаем по ширине
            self.orb_width_animation.setStartValue(current_width)
            self.orb_width_animation.setEndValue(50)

            # Затем по высоте до линии
            self.orb_animation.setStartValue(current_height)
            self.orb_animation.setEndValue(2)

            QTimer.singleShot(300, lambda: self.orb_animation.start())

            def on_hide_finished():
                self.orb_frame.hide()
                self.orb_animation_in_progress = False  # Сбрасываем защиту

            self.orb_animation.finished.connect(on_hide_finished)
            self._animation_connected = True
            self.orb_width_animation.start()

        if self.orb_visible:
            self.orb_animation.start()

    def _start_width_animation(self):
        """Запускает анимацию ширины с задержкой"""
        if hasattr(self, "orb_width_animation"):
            self.orb_width_animation.setStartValue(50)
            self.orb_width_animation.setEndValue(350)  # Полная ширина орба
            self.orb_width_animation.start()

    # Метод toggle_play_pause удален - теперь управление аудио в ChatPanel

    def add_system_message(self, message: str, timeout: int = 5000):
        """Forward system notifications to chat as inline messages.

        For compatibility, if ChatPanel is not set, does nothing (no separate UI panel).
        """
        try:
            if self._chat_panel is not None and hasattr(self._chat_panel, "add_system_message"):
                self._chat_panel.add_system_message(message)
                return
        except Exception:
            pass

        # Fallback: no-op (notifications frame removed from main UI)
        return

    def remove_notification(self, notification_label):
        """Удалить уведомление"""
        if notification_label:
            self.notifications_layout.removeWidget(notification_label)
            notification_label.deleteLater()

            # Скрыть панель уведомлений если она пуста
            if self.notifications_layout.count() == 0:
                self.notifications_frame.hide()

    def _create_user_indicator(self) -> QFrame:
        """Create user indicator widget"""
        indicator_frame = QFrame()
        indicator_frame.setStyleSheet(
            """
            QFrame {
                background-color: rgba(60, 60, 60, 0.3);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 8px;
            }
        """
        )

        layout = QHBoxLayout()
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(10)

        # User icon
        self.user_icon_label = QLabel("👤")
        self.user_icon_label.setStyleSheet(
            """
            QLabel {
                color: white;
                font-size: 20px;
                background: transparent;
            }
        """
        )
        layout.addWidget(self.user_icon_label)

        # User info (username + role)
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)

        self.username_label = QLabel(_("Гость"))
        self.username_label.setStyleSheet(
            """
            QLabel {
                color: white;
                font-size: 13px;
                font-weight: bold;
                background: transparent;
            }
        """
        )
        info_layout.addWidget(self.username_label)

        self.role_label = QLabel(_("Роль: Гость"))
        self.role_label.setStyleSheet(
            """
            QLabel {
                color: rgba(255, 255, 255, 0.6);
                font-size: 11px;
                background: transparent;
            }
        """
        )
        info_layout.addWidget(self.role_label)

        self.subscription_label = QLabel("")
        self.subscription_label.setStyleSheet(
            """
            QLabel {
                color: rgba(180, 220, 255, 0.8);
                font-size: 10px;
                background: transparent;
            }
        """
        )
        self.subscription_label.hide()
        info_layout.addWidget(self.subscription_label)

        layout.addLayout(info_layout)
        layout.addStretch()

        # Manage users button (only for admins)
        self.manage_users_button = QPushButton("⚙️ " + _("Пользователи"))
        self.manage_users_button.setFixedHeight(30)
        self.manage_users_button.setStyleSheet(
            """
            QPushButton {
                background-color: rgba(74, 158, 255, 0.3);
                border: 1px solid rgba(74, 158, 255, 0.5);
                border-radius: 5px;
                color: white;
                font-size: 11px;
                padding: 5px 12px;
            }
            QPushButton:hover {
                background-color: rgba(74, 158, 255, 0.5);
            }
            QPushButton:pressed {
                background-color: rgba(74, 158, 255, 0.7);
            }
        """
        )
        self.manage_users_button.clicked.connect(self._open_user_management)
        self.manage_users_button.hide()  # Hidden by default, shown for admins
        layout.addWidget(self.manage_users_button)

        # Logout button
        self.logout_button = QPushButton("🚪 " + _("Выйти"))
        self.logout_button.setFixedHeight(30)
        self.logout_button.setStyleSheet(
            """
            QPushButton {
                background-color: rgba(255, 74, 74, 0.3);
                border: 1px solid rgba(255, 74, 74, 0.5);
                border-radius: 5px;
                color: white;
                font-size: 11px;
                padding: 5px 12px;
            }
            QPushButton:hover {
                background-color: rgba(255, 74, 74, 0.5);
            }
            QPushButton:pressed {
                background-color: rgba(255, 74, 74, 0.7);
            }
        """
        )
        self.logout_button.clicked.connect(self._handle_logout)
        self.logout_button.hide()  # Hidden for guest
        layout.addWidget(self.logout_button)

        indicator_frame.setLayout(layout)
        indicator_frame.hide()  # Hidden by default until login
        return indicator_frame

    def set_chat_panel(self, chat_panel: Any) -> None:
        """Attach ChatPanel to forward system messages to chat feed."""
        try:
            self._chat_panel = chat_panel
        except Exception:
            self._chat_panel = None

    def set_user_info(
        self,
        username: str,
        role: str,
        user_id: Optional[str] = None,
        subscription: Optional[str] = None,
    ):
        """Set user information in indicator"""
        from utils.security import Permission, Role, get_rbac_manager

        self.current_user_id = user_id
        self.current_username = username
        self.current_role = role

        # Update labels
        if not user_id:  # Guest
            self.username_label.setText(_("Гость"))
            self.role_label.setText(_("Роль: Гость"))
            self.user_icon_label.setText("👤")
            self.manage_users_button.hide()
            self.logout_button.hide()
            if subscription:
                self.subscription_label.setText(_("План: {plan}").format(plan=subscription))
                self.subscription_label.show()
            else:
                self.subscription_label.hide()
        else:
            self.username_label.setText(username)

            # Role display with color
            role_colors = {
                "guest": ("rgba(150, 150, 150, 1.0)", "👤"),
                "user": ("rgba(74, 158, 255, 1.0)", "👤"),
                "power_user": ("rgba(255, 154, 74, 1.0)", "⭐"),
                "admin": ("rgba(255, 74, 74, 1.0)", "👑"),
            }

            role_lower = role.lower().replace(" ", "_")
            color, icon = role_colors.get(role_lower, ("rgba(255, 255, 255, 0.8)", "👤"))

            self.role_label.setText(_("Роль: {role}").format(role=role))
            self.role_label.setStyleSheet(f"color: {color}; font-size: 11px; background: transparent;")
            self.user_icon_label.setText(icon)

            if subscription:
                self.subscription_label.setText(_("План: {plan}").format(plan=subscription))
                self.subscription_label.show()
            else:
                self.subscription_label.hide()

            # Show/hide manage users button for admins
            try:
                rbac = get_rbac_manager()
                rbac.set_current_user(user_id)
                # Check if user can view users (admin permission)
                is_admin = rbac.has_permission(Permission.USER_VIEW)
                self.manage_users_button.setVisible(is_admin)
            except Exception:
                self.manage_users_button.hide()

            self.logout_button.show()

        # Do not show indicator in main UI; moved to Settings
        try:
            ui = getattr(self, "user_indicator", None)
            if ui is not None:
                ui.hide()
        except Exception:
            pass

    def _open_user_management(self):
        """Open user management dialog"""
        try:
            from .user_management_dialog import UserManagementDialog

            if not self.current_user_id:
                return

            dialog = UserManagementDialog(self.current_user_id, self)
            dialog.exec()

        except Exception as e:
            self.logger.error(f"Failed to open user management: {e}")
            from PyQt6.QtWidgets import QMessageBox

            QMessageBox.critical(
                self, _("Ошибка"), _("Не удалось открыть управление пользователями:\n{error}").format(error=e)
            )

    def _handle_logout(self):
        """Handle logout button click"""
        from PyQt6.QtWidgets import QMessageBox

        reply = QMessageBox.question(
            self,
            _("Выход"),
            _("Вы уверены, что хотите выйти из системы?"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                # Clear user info
                self.current_user_id = None
                self.current_username = None
                self.current_role = None

                # Hide indicator (if exists)
                try:
                    ui = getattr(self, "user_indicator", None)
                    if ui is not None:
                        ui.hide()
                except Exception:
                    pass

                # Emit logout signal (will be caught by MainWindow)
                if hasattr(self, "logout_requested"):
                    self.logout_requested.emit()

                self.logger.info("User logged out")

            except Exception as e:
                self.logger.error(f"Logout error: {e}")
                QMessageBox.critical(self, _("Ошибка"), _("Не удалось выйти:\n{error}").format(error=e))
