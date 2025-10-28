"""
Enhanced Login Dialog with Role-Based Access and Guest Mode
Улучшенный диалог входа с ролевым доступом и гостевым режимом
"""

from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QPixmap
from PyQt6.QtWidgets import (
    QCheckBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from i18n import _
from utils.logger import ModuleLogger
from utils.security import Role, UserStorage, get_auth_manager


class EnhancedLoginDialog(QDialog):
    """Enhanced dialog for user authentication with guest mode and role-based access"""

    # Signals
    login_successful = pyqtSignal(str, str, str)  # user_id, username, role
    guest_mode_selected = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = ModuleLogger("EnhancedLoginDialog")
        self.auth_manager = get_auth_manager()
        self.selected_user_id = None
        self.selected_username = None
        self.selected_role = None
        self.guest_session_start = None
        self.init_ui()

    def init_ui(self):
        """Initialize UI"""
        self.setWindowTitle(_("Вход в Arvis"))
        self.setFixedSize(480, 650)  # Увеличен размер для корректного отображения
        self.setModal(True)

        # Frameless window
        try:
            # PyQt6-style flags if available
            self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)  # type: ignore[attr-defined]
        except Exception:
            self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)  # type: ignore[attr-defined]

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Title bar
        title_bar = self._create_title_bar()
        main_layout.addWidget(title_bar)

        # Content area
        content_widget = QWidget()
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(30, 20, 30, 20)
        content_layout.setSpacing(15)

        # Logo/Icon
        logo_label = QLabel("🔐")
        try:
            logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)  # type: ignore[attr-defined]
        except Exception:
            logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)  # type: ignore[attr-defined]
        logo_label.setStyleSheet(
            """
            QLabel {
                color: #4a9eff;
                font-size: 64px;
                background: transparent;
            }
        """
        )
        content_layout.addWidget(logo_label)

        # Title
        title_label = QLabel(_("Добро пожаловать в Arvis"))
        try:
            title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)  # type: ignore[attr-defined]
        except Exception:
            title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)  # type: ignore[attr-defined]
        title_label.setStyleSheet(
            """
            QLabel {
                color: white;
                font-size: 22px;
                font-weight: bold;
                background: transparent;
                margin-bottom: 5px;
            }
        """
        )
        content_layout.addWidget(title_label)

        # Subtitle
        subtitle_label = QLabel(_("Выберите способ входа"))
        try:
            subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)  # type: ignore[attr-defined]
        except Exception:
            subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)  # type: ignore[attr-defined]
        subtitle_label.setStyleSheet(
            """
            QLabel {
                color: rgba(255, 255, 255, 0.6);
                font-size: 13px;
                background: transparent;
                margin-bottom: 15px;
            }
        """
        )
        content_layout.addWidget(subtitle_label)

        # Username field
        username_layout = QVBoxLayout()
        username_layout.setSpacing(5)
        username_label = QLabel(_("Имя пользователя:"))
        username_label.setStyleSheet("color: rgba(255, 255, 255, 0.8); background: transparent;")
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText(_("Введите имя пользователя"))
        self.username_input.returnPressed.connect(self.handle_user_login)
        username_layout.addWidget(username_label)
        username_layout.addWidget(self.username_input)
        content_layout.addLayout(username_layout)

        # Password field
        password_layout = QVBoxLayout()
        password_layout.setSpacing(5)
        password_label = QLabel(_("Пароль:"))
        password_label.setStyleSheet("color: rgba(255, 255, 255, 0.8); background: transparent;")
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setPlaceholderText(_("Введите пароль"))
        self.password_input.returnPressed.connect(self.handle_user_login)
        password_layout.addWidget(password_label)
        password_layout.addWidget(self.password_input)
        content_layout.addLayout(password_layout)

        # Remember me checkbox
        self.remember_checkbox = QCheckBox(_("Запомнить меня"))
        self.remember_checkbox.setChecked(True)
        self.remember_checkbox.setStyleSheet(
            """
            QCheckBox {
                color: rgba(255, 255, 255, 0.7);
                background: transparent;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border: 1px solid rgba(255, 255, 255, 0.3);
                border-radius: 3px;
                background: rgba(60, 60, 60, 0.5);
            }
            QCheckBox::indicator:checked {
                background: #4a9eff;
                border-color: #4a9eff;
            }
        """
        )
        content_layout.addWidget(self.remember_checkbox)

        content_layout.addSpacing(5)

        # User Login button
        self.login_button = QPushButton(_("Войти"))
        self.login_button.setFixedHeight(45)
        self.login_button.setObjectName("login_button")
        self.login_button.clicked.connect(self.handle_user_login)
        content_layout.addWidget(self.login_button)

        # Separator
        separator = QLabel(_("или"))
        try:
            separator.setAlignment(Qt.AlignmentFlag.AlignCenter)  # type: ignore[attr-defined]
        except Exception:
            separator.setAlignment(Qt.AlignmentFlag.AlignCenter)  # type: ignore[attr-defined]
        separator.setStyleSheet(
            """
            QLabel {
                color: rgba(255, 255, 255, 0.4);
                font-size: 12px;
                background: transparent;
                margin: 5px 0;
            }
        """
        )
        content_layout.addWidget(separator)

        # Guest mode button with info
        guest_info_widget = QWidget()
        guest_info_layout = QVBoxLayout()
        guest_info_layout.setSpacing(8)
        guest_info_layout.setContentsMargins(0, 0, 0, 0)

        self.guest_button = QPushButton(_("🎭 Войти как гость"))
        self.guest_button.setFixedHeight(40)
        self.guest_button.setObjectName("guest_button")
        self.guest_button.clicked.connect(self.handle_guest_login)
        guest_info_layout.addWidget(self.guest_button)

        # Guest mode restrictions info
        guest_info = QLabel(_("• Ограничено 30 минут\n• Базовые функции\n• Без сохранения истории"))
        try:
            guest_info.setAlignment(Qt.AlignmentFlag.AlignLeft)  # type: ignore[attr-defined]
        except Exception:
            guest_info.setAlignment(Qt.AlignmentFlag.AlignLeft)  # type: ignore[attr-defined]
        guest_info.setStyleSheet(
            """
            QLabel {
                color: rgba(255, 255, 255, 0.5);
                font-size: 11px;
                background: transparent;
                padding: 5px 10px;
                border-left: 2px solid rgba(255, 255, 255, 0.2);
            }
        """
        )
        guest_info_layout.addWidget(guest_info)

        guest_info_widget.setLayout(guest_info_layout)
        content_layout.addWidget(guest_info_widget)

        # Create account link (for alpha/beta testers)
        create_account_label = QLabel(
            _("<a href='#' style='color: #4a9eff; text-decoration: none;'>Создать аккаунт</a>")
        )
        try:
            create_account_label.setAlignment(Qt.AlignmentFlag.AlignCenter)  # type: ignore[attr-defined]
        except Exception:
            create_account_label.setAlignment(Qt.AlignmentFlag.AlignCenter)  # type: ignore[attr-defined]
        create_account_label.setStyleSheet("background: transparent; font-size: 12px;")
        create_account_label.linkActivated.connect(lambda: self.show_create_account())
        content_layout.addWidget(create_account_label)

        content_widget.setLayout(content_layout)
        main_layout.addWidget(content_widget)

        self.setLayout(main_layout)

        # Apply styles
        self.apply_styles()

    def _create_title_bar(self) -> QWidget:
        """Create custom title bar"""
        title_bar = QWidget()
        title_bar.setFixedHeight(30)
        title_bar.setStyleSheet(
            """
            QWidget {
                background-color: rgb(43, 43, 43);
                border-bottom: 1px solid rgb(60, 60, 60);
            }
        """
        )

        layout = QHBoxLayout()
        layout.setContentsMargins(10, 0, 0, 0)

        # Title
        title_label = QLabel(_("Аутентификация Arvis"))
        title_label.setStyleSheet(
            """
            QLabel {
                color: white;
                font-weight: bold;
                font-size: 12px;
                border: none;
            }
        """
        )

        layout.addWidget(title_label)
        layout.addStretch()

        # Close button
        close_btn = QPushButton("×")
        close_btn.setFixedSize(30, 30)
        close_btn.setStyleSheet(
            """
            QPushButton {
                background-color: rgb(43, 43, 43);
                color: rgb(180, 180, 180);
                border: none;
                font-size: 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgb(232, 17, 35);
                color: white;
            }
            QPushButton:pressed {
                background-color: rgb(180, 30, 30);
            }
        """
        )
        close_btn.clicked.connect(self.reject)
        layout.addWidget(close_btn)

        title_bar.setLayout(layout)

        # Make draggable
        title_bar.mousePressEvent = self._title_bar_mouse_press  # type: ignore[assignment]
        title_bar.mouseMoveEvent = self._title_bar_mouse_move  # type: ignore[assignment]

        return title_bar

    def _title_bar_mouse_press(self, event):
        """Handle title bar mouse press"""
        if event.button() == Qt.LeftButton:  # type: ignore[attr-defined]
            self.drag_pos = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def _title_bar_mouse_move(self, event):
        """Handle title bar mouse move"""
        if event.buttons() == Qt.LeftButton and hasattr(self, "drag_pos"):  # type: ignore[attr-defined]
            self.move(event.globalPos() - self.drag_pos)
            event.accept()

    def apply_styles(self):
        """Apply dialog styles"""
        self.setStyleSheet(
            """
            QDialog {
                background-color: rgb(43, 43, 43);
            }

            QLineEdit {
                background-color: rgba(60, 60, 60, 0.5);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 5px;
                padding: 10px 12px;
                color: white;
                font-size: 13px;
            }

            QLineEdit:focus {
                border: 1px solid #4a9eff;
                background-color: rgba(60, 60, 60, 0.8);
            }

            QPushButton#login_button {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #5aa9ff, stop:1 #4a9eff);
                color: white;
                border: none;
                border-radius: 5px;
                padding: 12px;
                font-size: 14px;
                font-weight: bold;
            }

            QPushButton#login_button:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #6ab9ff, stop:1 #5aa9ff);
            }

            QPushButton#login_button:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #3a8eff, stop:1 #2a7eff);
            }

            QPushButton#guest_button {
                background-color: transparent;
                color: rgba(255, 255, 255, 0.7);
                border: 2px dashed rgba(255, 255, 255, 0.3);
                border-radius: 5px;
                padding: 10px;
                font-size: 13px;
                font-weight: bold;
            }

            QPushButton#guest_button:hover {
                background-color: rgba(255, 255, 255, 0.05);
                color: rgba(255, 255, 255, 0.9);
                border-color: rgba(255, 255, 255, 0.5);
            }
        """
        )

    def handle_user_login(self):
        """Handle user login button click"""
        username = self.username_input.text().strip()
        password = self.password_input.text()

        if not username or not password:
            QMessageBox.warning(self, _("Ошибка"), _("Пожалуйста, заполните все поля"))
            return

        try:
            # Authenticate (local)
            session = self.auth_manager.authenticate(username, password)

            if session:
                user = self.auth_manager.validate_session(session.session_id)
                if user:
                    self.logger.info(f"User authenticated: {username} (Role: {user.role.value})")

                    # Check if 2FA is enabled
                    if user.require_2fa:
                        from src.gui.two_factor_verification_dialog import TwoFactorVerificationDialog
                        storage = UserStorage()
                        verify_dialog = TwoFactorVerificationDialog(self, user, storage)
                        if verify_dialog.exec() == QDialog.DialogCode.Accepted:
                            self._complete_login(user, session.session_id)
                        else:
                            self.password_input.clear(); self.password_input.setFocus()
                    else:
                        self._complete_login(user, session.session_id)
                else:
                    QMessageBox.warning(self, _("Ошибка входа"), _("Не удалось создать сессию"))
            else:
                QMessageBox.warning(self, _("Ошибка входа"), _("Неверное имя пользователя или пароль"))
                self.password_input.clear(); self.password_input.setFocus()

        except PermissionError as e:
            QMessageBox.warning(self, _("Ошибка"), str(e))
            self.password_input.clear(); self.password_input.setFocus()
        except Exception as e:
            self.logger.error(f"Login error: {e}")
            QMessageBox.critical(self, _("Ошибка"), _("Не удалось выполнить вход:\n{error}").format(error=str(e)))

    def _complete_login(self, user, session_id):
        """Complete login process after authentication"""
        self.selected_user_id = user.user_id
        self.selected_username = user.username
        self.selected_role = user.role.value

        # Emit success signal
        self.login_successful.emit(user.user_id, user.username, user.role.value)
        self.accept()

    # Removed remote-complete; local flow only for stability

    def handle_guest_login(self):
        """Handle guest mode login"""
        try:
            reply = QMessageBox.question(
                self,
                _("Гостевой режим"),
                _(
                    "Войти как гость?\n\n"
                    "Ограничения:\n"
                    "• Сеанс ограничен 30 минутами\n"
                    "• Доступны только базовые функции\n"
                    "• История не сохраняется\n"
                    "• Нет доступа к системным функциям"
                ),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )

            if reply == QMessageBox.StandardButton.Yes:
                self.logger.info("Guest mode login selected")
                self.selected_user_id = "guest"
                self.selected_username = "Guest"
                self.selected_role = Role.GUEST.value
                self.guest_session_start = datetime.now()

                # Emit guest signal
                self.guest_mode_selected.emit()
                self.login_successful.emit("guest", "Guest", Role.GUEST.value)
                self.accept()

        except Exception as e:
            self.logger.error(f"Guest login error: {e}")
            QMessageBox.critical(
                self,
                _("Ошибка"),
                _("Не удалось войти в гостевом режиме:\n{error}").format(error=str(e)),
            )

    def show_create_account(self):
        """Show create account dialog"""
        try:
            from src.gui.login_dialog import CreateAccountDialog

            dialog = CreateAccountDialog(self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                # Account created, try to login
                user_id, username = dialog.get_credentials()
                if user_id:
                    # Get user role
                    storage = UserStorage()
                    user = storage.get_user_by_id(user_id)
                    if user:
                        self.selected_user_id = user_id
                        self.selected_username = username
                        self.selected_role = user.role.value
                        self.login_successful.emit(user_id, username, user.role.value)
                        self.accept()

        except Exception as e:
            self.logger.error(f"Create account error: {e}")
            QMessageBox.critical(
                self,
                _("Ошибка"),
                _("Не удалось создать аккаунт:\n{error}").format(error=str(e)),
            )

    def get_credentials(self):
        """Get selected user credentials and role"""
        return self.selected_user_id, self.selected_username, self.selected_role

    def is_guest_session_expired(self) -> bool:
        """Check if guest session has expired (30 minutes)"""
        if not self.guest_session_start:
            return False
        elapsed = datetime.now() - self.guest_session_start
        return elapsed > timedelta(minutes=30)
