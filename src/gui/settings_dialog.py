"""
Settings dialog for Arvis application
"""

from pathlib import Path

from PyQt6.QtCore import QRect, QRectF, Qt, pyqtSignal
from PyQt6.QtGui import QFont, QPainterPath, QRegion
from PyQt6.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QDialog,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSlider,
    QSpinBox,
    QStyle,
    QStyleOptionTab,
    QStylePainter,
    QTabBar,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from config.config import Config


class SettingsDialog(QDialog):
    """Settings configuration dialog"""

    settings_changed = pyqtSignal(dict)

    def __init__(self, config: Config, parent=None):
        super().__init__(parent)
        self.config = config
        self.current_user_id = None  # Will be set if authentication is enabled
        self.init_ui()
        self.load_settings()

    def set_current_user(self, user_id):
        """Установить текущего пользователя для вкладки безопасности"""
        self.current_user_id = user_id

    def init_ui(self):
        """Initialize settings dialog UI"""
        self.setWindowTitle("Настройки Arvis")
        # Увеличиваем окно в ширину
        self.setFixedSize(760, 620)
        self.setModal(True)

        # Remove default title bar and add custom one
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)  # type: ignore[attr-defined]
        self.create_title_bar()

        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Add title bar
        main_layout.addWidget(self.title_bar)

        # Content layout
        layout = QVBoxLayout()
        # Прижимаем слева
        layout.setContentsMargins(0, 10, 10, 10)

        # Контент: слева вертикальные кнопки разделов, справа содержимое вкладок
        from PyQt6.QtWidgets import QStackedWidget

        # Create horizontal layout for nav + content
        tabs_layout = QHBoxLayout()
        tabs_layout.setContentsMargins(0, 0, 0, 0)
        # Единый отступ между кнопками разделов и содержимым
        tabs_layout.setSpacing(12)

        # Left side: vertical option buttons styled with SVG background
        nav_container = QWidget()
        # Убираем фоновый прямоугольник под кнопками
        try:
            nav_container.setStyleSheet("background: transparent;")
        except Exception:
            pass
        nav_container.setFixedWidth(180)
        nav_layout = QVBoxLayout()
        nav_layout.setContentsMargins(0, 0, 0, 0)
        nav_layout.setSpacing(5)

        class OptionButton(QPushButton):
            def __init__(self, text: str):
                super().__init__(text)
                self.setCheckable(True)
                self.setMinimumHeight(44)
                try:
                    self.setFocusPolicy(Qt.NoFocus)  # type: ignore[attr-defined]
                except Exception:
                    pass
                # Прозрачный фон и скругление через маску
                try:
                    self.setAttribute(Qt.WA_TranslucentBackground, True)  # type: ignore[attr-defined]
                except Exception:
                    pass
                self.setStyleSheet(
                    """
                    QPushButton {
                        border: none;
                        border-image: none;
                        background-color: transparent;
                        /* Используем 9-slice, чтобы скругления не искажались */
                        color: white;
                        padding: 8px 12px;
                        font-size: 12px;
                        border-top-left-radius: 0px;
                        border-bottom-left-radius: 0px;
                        border-top-right-radius: 16px;
                        border-bottom-right-radius: 16px;
                    }
                    QPushButton:hover {
                        /* Без подсветки на hover */
                        background-color: transparent;
                        border-image: none;
                    }
                    QPushButton:pressed {
                        /* Лёгкая реакция по тексту без фона */
                        background-color: transparent;
                        border-image: none;
                        color: #e6e6e6;
                    }
                    QPushButton:checked {
                        /* Активное состояние: светлый вариант и тёмный текст */
                        background-color: transparent;
                        border-image: none;
                        color: #1a1a1a;
                        font-weight: bold;
                        border-top-left-radius: 0px;
                        border-bottom-left-radius: 0px;
                        border-top-right-radius: 16px;
                        border-bottom-right-radius: 16px;
                    }
                    QPushButton:focus { outline: none; }
                    """
                )

            def paintEvent(self, event):
                # Кастомная отрисовка: фон-картинка + текст заголовка раздела
                from PyQt6.QtGui import QColor, QFontMetrics, QPainter, QPen, QPixmap

                painter = QStylePainter(self)

                # Фон кнопки (разные варианты для checked/unchecked)
                image_path = "UXUI/Button/Button_optiB2.svg" if self.isChecked() else "UXUI/Button/Button_optiB.svg"
                pixmap = QPixmap(image_path)
                target_rect = self.rect()
                if not pixmap.isNull():
                    painter.drawPixmap(target_rect, pixmap)

                # Текст кнопки (название раздела)
                text_color = QColor("#1a1a1a") if self.isChecked() else QColor("white")
                painter.setPen(QPen(text_color))
                # Небольшой отступ слева, чтобы текст не лип к краю
                text_rect = target_rect.adjusted(16, 0, -10, 0)
                try:
                    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
                except Exception:
                    try:
                        painter.setRenderHint(QPainter.Antialiasing, True)  # type: ignore[attr-defined]
                    except Exception:
                        pass
                painter.drawText(text_rect, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, self.text())  # type: ignore[attr-defined]

            def resizeEvent(self, event):
                # Маска с плоской левой стороной и скруглением 16px справа
                try:
                    r = self.rect()
                    x, y, w, h = r.x(), r.y(), r.width(), r.height()
                    tr = 16.0
                    br = 16.0
                    path = QPainterPath()
                    # Начало сверху слева
                    path.moveTo(x, y)
                    # Верхняя кромка до правого скругления
                    path.lineTo(x + w - tr, y)
                    # Верхний правый угол
                    path.quadTo(x + w, y, x + w, y + tr)
                    # Правая кромка
                    path.lineTo(x + w, y + h - br)
                    # Нижний правый угол
                    path.quadTo(x + w, y + h, x + w - br, y + h)
                    # Нижняя кромка до левого края
                    path.lineTo(x, y + h)
                    # Левая кромка вверх (без скругления)
                    path.lineTo(x, y)
                    path.closeSubpath()
                    region = QRegion(path.toFillPolygon().toPolygon())
                    self.setMask(region)
                except Exception:
                    pass
                return super().resizeEvent(event)

        self._nav_group = QButtonGroup(self)
        self._nav_group.setExclusive(True)
        self._nav_buttons = []
        sections = ["Общие", "LLM", "TTS | STT", "Язык", "Модули", "Пользователи", "Расширенные"]
        for i, name in enumerate(sections):
            btn = OptionButton(name)
            self._nav_group.addButton(btn, i)
            self._nav_buttons.append(btn)
            nav_layout.addWidget(btn)
        nav_layout.addStretch()
        nav_container.setLayout(nav_layout)

        # Right side: stacked widget with tab content
        self.tab_stack = QStackedWidget()

        tabs_layout.addWidget(nav_container)
        tabs_layout.addWidget(self.tab_stack)

        # Container widget for the tabs layout
        tabs_container = QWidget()
        try:
            tabs_container.setStyleSheet("background: transparent;")
        except Exception:
            pass
        tabs_container.setLayout(tabs_layout)

        # Create tabs and add to stack
        self.create_all_tabs()

        layout.addWidget(tabs_container)

        # Buttons
        buttons_layout = QHBoxLayout()

        self.save_button = QPushButton("Сохранить")
        self.save_button.clicked.connect(self.save_settings)

        self.cancel_button = QPushButton("Отмена")
        self.cancel_button.clicked.connect(self.reject)

        self.apply_button = QPushButton("Сохранить и перезагрузить")
        self.apply_button.setToolTip("Сохранить изменения и перезапустить приложение")
        self.apply_button.clicked.connect(self.handle_reload_click)

        buttons_layout.addStretch()
        buttons_layout.addWidget(self.save_button)
        buttons_layout.addWidget(self.cancel_button)
        buttons_layout.addWidget(self.apply_button)

        layout.addLayout(buttons_layout)

        # Content widget
        content_widget = QWidget()
        content_widget.setLayout(layout)
        main_layout.addWidget(content_widget)

        self.setLayout(main_layout)

        # Инициализируем выбор первой вкладки
        first_btn = self._nav_group.button(0)
        if first_btn is not None:
            first_btn.setChecked(True)
        # PyQt6: use idClicked(int) instead of deprecated indexed signal syntax
        try:
            self._nav_group.idClicked.connect(self.change_tab)
        except Exception:
            # Fallback for environments exposing only buttonClicked with button parameter
            try:
                self._nav_group.buttonClicked.connect(
                    lambda btn: self.change_tab(self._nav_group.id(btn))
                )
            except Exception:
                pass

        # Apply dark theme
        self.setStyleSheet(
            """
            QDialog {
                background-color: rgb(43, 43, 43);
                color: white;
            }
            QTabWidget::pane {
                border: 1px solid rgb(60, 60, 60);
                background-color: rgb(43, 43, 43);
            }
            QTabBar::tab {
                background-color: rgb(60, 60, 60);
                color: white;
                padding: 8px 16px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: rgb(80, 80, 80);
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid rgb(60, 60, 60);
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            /* Единый стиль контролов для всех вкладок настроек */
            QLineEdit, QComboBox, QSpinBox {
                background-color: rgb(50, 50, 50);
                border: 1px solid rgb(70, 70, 70);
                border-radius: 5px;
                padding: 4px 8px;
                color: white;
            }
            QComboBox QAbstractItemView {
                background-color: rgb(50, 50, 50);
                selection-background-color: rgb(70, 70, 70);
                color: white;
                border: 1px solid rgb(70, 70, 70);
            }
            QCheckBox { color: white; }
            /* Базовые кнопки внутри диалога (не влияет на кнопки навигации и заголовка) */
            QWidget > QPushButton {
                background-color: rgb(60, 60, 60);
                color: white;
                border: 1px solid rgb(80, 80, 80);
                border-radius: 5px;
                padding: 6px 10px;
            }
            QWidget > QPushButton:hover {
                background-color: rgb(70, 70, 70);
            }
            QWidget > QPushButton:pressed {
                background-color: rgb(50, 50, 50);
            }
        """
        )

    def change_tab(self, index):
        """Change the displayed tab based on list selection"""
        self.tab_stack.setCurrentIndex(index)

    def create_all_tabs(self):
        """Create all tabs and add them to the stack widget"""
        self.tab_stack.addWidget(self.create_general_tab())
        self.tab_stack.addWidget(self.create_llm_tab())
        self.tab_stack.addWidget(self.create_tts_stt_tab())
        self.tab_stack.addWidget(self.create_language_tab())
        self.tab_stack.addWidget(self.create_modules_tab())
        self.tab_stack.addWidget(self.create_users_tab())
        self.tab_stack.addWidget(self.create_advanced_tab())

    def handle_reload_click(self):
        """Save settings and trigger application restart via parent MainWindow."""
        # Сначала сохраняем текущие настройки (без всплывающего окна)
        self.apply_settings(silent=True)
        # На всякий случай сбрасываем изменения на диск ещё раз (избыточно, но надёжно)
        try:
            self.config.save_config()
        except Exception:
            pass
        # Notify the parent window to restart
        parent = self.parent()
        try:
            # If parent is MainWindow, call its restart_application
            if parent:
                restart_cb = getattr(parent, "restart_application", None)
                if callable(restart_cb):
                    restart_cb()
            else:
                # Fallback: accept dialog, actual restart can be handled by caller
                self.accept()
        except Exception:
            self.accept()

    def create_title_bar(self):
        """Create custom title bar for settings dialog"""
        self.title_bar = QWidget()
        self.title_bar.setFixedHeight(30)
        self.title_bar.setStyleSheet(
            """
            QWidget {
                background-color: rgb(43, 43, 43);
                border-bottom: 1px solid rgb(60, 60, 60);
            }
        """
        )

        # Title bar layout
        title_layout = QHBoxLayout()
        title_layout.setContentsMargins(10, 0, 0, 0)

        # Title text
        self.title_label = QLabel("Настройки Arvis")
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

        # Close button
        self.close_btn = QPushButton("×")
        self.close_btn.setStyleSheet(
            """
            QPushButton {
                background-color: rgb(43, 43, 43);
                color: rgb(80, 80, 80);
                border: none;
                font-size: 16px;
                font-weight: bold;
                width: 30px;
                height: 30px;
            }
            QPushButton:hover {
                background-color: rgb(200, 50, 50);
                color: white;
            }
            QPushButton:pressed {
                background-color: rgb(180, 30, 30);
            }
        """
        )

        self.close_btn.clicked.connect(self._on_close_clicked)
        title_layout.addWidget(self.close_btn)

        self.title_bar.setLayout(title_layout)

        # Make title bar draggable
        self.title_bar.mousePressEvent = self.title_bar_mouse_press  # type: ignore[assignment]
        self.title_bar.mouseMoveEvent = self.title_bar_mouse_move  # type: ignore[assignment]

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

    def _on_close_clicked(self) -> None:
        """Close dialog from title bar button click."""
        self.close()

    def create_general_tab(self):
        """Create general settings tab"""
        tab = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        # User settings group
        user_group = QGroupBox("Пользователь")
        # Гарантируем одинаковое оформление, как в остальных разделах
        user_group.setFlat(False)
        user_group.setStyleSheet(
            """
            QGroupBox {
                font-weight: bold;
                border: 2px solid rgb(60, 60, 60);
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            """
        )
        user_layout = QVBoxLayout()
        user_layout.setContentsMargins(10, 10, 10, 10)
        user_layout.setSpacing(8)

        # User name
        name_layout = QHBoxLayout()
        name_layout.setContentsMargins(0, 0, 0, 0)
        name_layout.setSpacing(8)
        name_label = QLabel("Имя:")
        name_label.setFixedWidth(120)
        name_layout.addWidget(name_label)
        self.name_edit = QLineEdit()
        name_layout.addWidget(self.name_edit)
        user_layout.addLayout(name_layout)

        # User city
        city_layout = QHBoxLayout()
        city_layout.setContentsMargins(0, 0, 0, 0)
        city_layout.setSpacing(8)
        city_label = QLabel("Город:")
        city_label.setFixedWidth(120)
        city_layout.addWidget(city_label)
        self.city_edit = QLineEdit()
        city_layout.addWidget(self.city_edit)
        user_layout.addLayout(city_layout)

        user_group.setLayout(user_layout)

        # Startup settings group
        startup_group = QGroupBox("Запуск")
        # То же оформление, что и у других вкладок
        startup_group.setFlat(False)
        startup_group.setStyleSheet(
            """
            QGroupBox {
                font-weight: bold;
                border: 2px solid rgb(60, 60, 60);
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            """
        )
        startup_layout = QVBoxLayout()
        startup_layout.setContentsMargins(10, 10, 10, 10)
        startup_layout.setSpacing(6)

        self.autostart_ollama = QCheckBox("Автозапуск Ollama")
        self.preload_model = QCheckBox("Предзагрузка модели")
        self.minimize_to_tray = QCheckBox("Сворачивать в трей")
        # Новый параметр: автозапуск Arvis вместе с Windows
        self.autostart_app = QCheckBox("Автозапуск Arvis вместе с системой")

        startup_layout.addWidget(self.autostart_ollama)
        startup_layout.addWidget(self.preload_model)
        startup_layout.addWidget(self.minimize_to_tray)
        startup_layout.addWidget(self.autostart_app)

        startup_group.setLayout(startup_layout)

        layout.addWidget(user_group)
        layout.addWidget(startup_group)
        layout.addStretch()

        tab.setLayout(layout)
        return tab

    def create_llm_tab(self):
        """Create LLM settings tab"""
        tab = QWidget()
        layout = QVBoxLayout()

        # Ollama settings group
        ollama_group = QGroupBox("Ollama")
        ollama_layout = QVBoxLayout()

        # Server URL
        url_layout = QHBoxLayout()
        url_layout.addWidget(QLabel("URL сервера:"))
        self.ollama_url_edit = QLineEdit()
        url_layout.addWidget(self.ollama_url_edit)
        ollama_layout.addLayout(url_layout)

        # Default model
        model_layout = QHBoxLayout()
        model_layout.addWidget(QLabel("Модель по умолчанию:"))
        self.default_model_combo = QComboBox()
        self.default_model_combo.addItems(["mistral:7b", "gemma2:2b"])
        model_layout.addWidget(self.default_model_combo)
        ollama_layout.addLayout(model_layout)

        ollama_group.setLayout(ollama_layout)

        # Generation settings group
        generation_group = QGroupBox("Генерация")
        generation_layout = QVBoxLayout()

        # Temperature
        temp_layout = QHBoxLayout()
        temp_layout.addWidget(QLabel("Температура:"))
        self.temperature_slider = QSlider(Qt.Orientation.Horizontal)
        self.temperature_slider.setMinimum(0)
        self.temperature_slider.setMaximum(200)
        self.temperature_slider.setValue(70)
        self.temp_label = QLabel("0.7")
        self.temperature_slider.valueChanged.connect(lambda v: self.temp_label.setText(f"{v/100:.1f}"))
        temp_layout.addWidget(self.temperature_slider)
        temp_layout.addWidget(self.temp_label)
        generation_layout.addLayout(temp_layout)

        # Max tokens
        tokens_layout = QHBoxLayout()
        tokens_layout.addWidget(QLabel("Макс. токенов:"))
        self.max_tokens_spin = QSpinBox()
        self.max_tokens_spin.setMinimum(256)
        self.max_tokens_spin.setMaximum(8192)
        self.max_tokens_spin.setValue(2048)
        tokens_layout.addWidget(self.max_tokens_spin)
        generation_layout.addLayout(tokens_layout)

        generation_group.setLayout(generation_layout)

        # Streaming / Output group
        stream_group = QGroupBox("Вывод ответа")
        stream_layout = QVBoxLayout()

        mode_layout = QHBoxLayout()
        mode_layout.addWidget(QLabel("Режим:"))
        self.stream_mode_combo = QComboBox()
        self.stream_mode_combo.addItems(["Реальный стрим", "Симуляция (после генерации)", "Отключено"])
        mode_layout.addWidget(self.stream_mode_combo)
        stream_layout.addLayout(mode_layout)
        stream_group.setLayout(stream_layout)

        layout.addWidget(ollama_group)
        layout.addWidget(generation_group)
        layout.addWidget(stream_group)
        layout.addStretch()

        tab.setLayout(layout)
        return tab

    def create_tts_stt_tab(self):
        """Create TTS/STT settings tab"""
        tab = QWidget()
        layout = QVBoxLayout()

        # TTS settings group
        tts_group = QGroupBox("Text-to-Speech")
        tts_layout = QVBoxLayout()

        # TTS Engine selector
        engine_layout = QHBoxLayout()
        engine_layout.addWidget(QLabel("Движок:"))
        self.tts_engine_combo = QComboBox()
        try:
            from modules.tts_factory import TTSFactory
            available = set((TTSFactory.list_available_engines() or []))
        except Exception:
            available = {"silero"}
        # Build engine entries with availability note
        engine_items = [
            ("silero", "Silero (русский, украинский)"),
            ("bark", "Bark (EN, RU/UK мультиязык)" + (" — не установлен" if "bark" not in available else "")),
        ]
        for key, label in engine_items:
            self.tts_engine_combo.addItem(label, key)
        
        # Add info button for Bark setup
        bark_info_btn = QPushButton("?")
        bark_info_btn.setMaximumWidth(30)
        bark_info_btn.setToolTip("Информация об установке Bark")
        def show_bark_info():
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.information(
                self,
                "Bark TTS Setup",
                "Для установки Bark TTS запустите:\n\n"
                "  pip install bark-ml\n\n"
                "Bark поддерживает:\n"
                "• Английский (англоязычные голоса - родные)\n"
                "• Русский (мультиязычные голоса)\n"
                "• Украинский (мультиязычные голоса)\n\n"
                "Примечание: Bark требует больше ресурсов, чем Silero."
            )
        bark_info_btn.clicked.connect(show_bark_info)
        
        engine_layout.addWidget(self.tts_engine_combo)
        engine_layout.addWidget(bark_info_btn)
        engine_layout.addStretch()
        tts_layout.addLayout(engine_layout)

        # Voice selection (tagged by engine)
        voice_layout = QHBoxLayout()
        voice_layout.addWidget(QLabel("Голос:"))
        self.voice_combo = QComboBox()
        voice_layout.addWidget(self.voice_combo)
        tts_layout.addLayout(voice_layout)

        # Predefine voices per engine with labels containing tags
        self._tts_voices_map = {
            "silero": [
                ("ru_v3", "[Silero] ru_v3 — профиль по умолчанию"),
                ("aidar", "[Silero] aidar — мужской"),
                ("eugene", "[Silero] eugene — мужской"),
                ("baya", "[Silero] baya — женский"),
                ("kseniya", "[Silero] kseniya — женский"),
                ("xenia", "[Silero] xenia — женский"),
            ],
            "bark": [
                # English speakers (Bark native)
                ("v2/en_speaker_0", "[Bark] en_speaker_0 — English (male)"),
                ("v2/en_speaker_1", "[Bark] en_speaker_1 — English (female)"),
                ("v2/en_speaker_2", "[Bark] en_speaker_2 — English (male)"),
                ("v2/en_speaker_3", "[Bark] en_speaker_3 — English (female)"),
                ("v2/en_speaker_4", "[Bark] en_speaker_4 — English (male)"),
                ("v2/en_speaker_5", "[Bark] en_speaker_5 — English (female)"),
                ("v2/en_speaker_6", "[Bark] en_speaker_6 — English (male)"),
                ("v2/en_speaker_7", "[Bark] en_speaker_7 — English (female)"),
                ("v2/en_speaker_8", "[Bark] en_speaker_8 — English (male)"),
                ("v2/en_speaker_9", "[Bark] en_speaker_9 — English (female)"),
                # Multilingual voices (experimental)
                ("v2/multilingual_00", "[Bark] multilingual_00 — мультиязык (RU/UK/EN)"),
                ("v2/multilingual_01", "[Bark] multilingual_01 — мультиязык (RU/UK/EN)"),
            ],
        }

        # Helper to repopulate voices according to selected engine
        def repopulate_voices_for_engine(engine_key: str):
            self.voice_combo.clear()
            items = self._tts_voices_map.get(engine_key, [])
            for val, label in items:
                self.voice_combo.addItem(label, val)
            # Select from config if available
            if engine_key == "silero":
                current = str(self.config.get("tts.voice", "ru_v3") or "ru_v3")
            else:
                current = str(self.config.get("tts.bark.voice", "v2/en_speaker_0") or "v2/en_speaker_0")
            idx = next((i for i in range(self.voice_combo.count()) if self.voice_combo.itemData(i) == current), -1)
            if idx >= 0:
                self.voice_combo.setCurrentIndex(idx)

        # Set current engine from config and populate voices
        current_engine = str(self.config.get("tts.default_engine", "silero") or "silero").lower()
        idx_engine = next((i for i in range(self.tts_engine_combo.count()) if self.tts_engine_combo.itemData(i) == current_engine), 0)
        self.tts_engine_combo.setCurrentIndex(idx_engine)
        repopulate_voices_for_engine(current_engine)

        # React to engine change
        def on_engine_changed(_index: int):
            eng = str(self.tts_engine_combo.currentData() or "silero")
            repopulate_voices_for_engine(eng)
        self.tts_engine_combo.currentIndexChanged.connect(on_engine_changed)

        # Sample rate
        rate_layout = QHBoxLayout()
        rate_layout.addWidget(QLabel("Частота:"))
        self.sample_rate_combo = QComboBox()
        self.sample_rate_combo.addItems(["8000", "24000", "48000"])
        self.sample_rate_combo.setCurrentText("48000")
        rate_layout.addWidget(self.sample_rate_combo)
        tts_layout.addLayout(rate_layout)

        # TTS Mode selection
        mode_layout = QHBoxLayout()
        mode_layout.addWidget(QLabel("Режим озвучки:"))
        self.tts_mode_combo = QComboBox()
        self.tts_mode_combo.addItems(["Реальное время (стрим)", "По предложениям", "После завершения"])
        self.tts_mode_combo.setCurrentIndex(0)  # Реальное время по умолчанию
        mode_layout.addWidget(self.tts_mode_combo)
        tts_layout.addLayout(mode_layout)

        # Enable TTS checkbox
        self.enable_tts_checkbox = QCheckBox("Озвучивать сгенерированный текст")
        self.enable_tts_checkbox.setChecked(True)  # По умолчанию включено
        self.enable_tts_checkbox.setToolTip("Автоматически озвучивать ответы ИИ через TTS")
        tts_layout.addWidget(self.enable_tts_checkbox)

        # Allow SAPI fallback (Windows)
        self.sapi_checkbox = QCheckBox("Разрешить SAPI (Windows) как запасной вариант")
        self.sapi_checkbox.setToolTip(
            "Если Silero недоступен или воспроизведение не удалось, использовать системный движок SAPI для озвучки"
        )
        self.sapi_checkbox.setChecked(True)
        tts_layout.addWidget(self.sapi_checkbox)

        tts_group.setLayout(tts_layout)

        # STT settings group
        stt_group = QGroupBox("Speech-to-Text")
        stt_layout = QVBoxLayout()

        # STT Engine (fixed to Vosk)
        stt_engine_layout = QHBoxLayout()
        stt_engine_layout.addWidget(QLabel("Движок:"))
        stt_engine_label = QLabel("Vosk")
        stt_engine_layout.addWidget(stt_engine_label)
        stt_engine_layout.addStretch()
        stt_layout.addLayout(stt_engine_layout)

        # Wake word
        wake_layout = QHBoxLayout()
        wake_layout.addWidget(QLabel("Слово активации:"))
        self.wake_word_edit = QLineEdit()
        wake_layout.addWidget(self.wake_word_edit)
        stt_layout.addLayout(wake_layout)

        # Model path
        model_layout = QHBoxLayout()
        model_layout.addWidget(QLabel("Путь к модели:"))
        self.model_path_edit = QLineEdit()
        self.model_browse_button = QPushButton("Обзор...")
        self.model_browse_button.clicked.connect(self.browse_model_path)
        model_layout.addWidget(self.model_path_edit)
        model_layout.addWidget(self.model_browse_button)
        stt_layout.addLayout(model_layout)

        stt_group.setLayout(stt_layout)

        layout.addWidget(tts_group)
        layout.addWidget(stt_group)
        layout.addStretch()

        tab.setLayout(layout)
        return tab

    def create_language_tab(self):
        """Create language settings tab for UI and Speech (TTS/STT)"""
        tab = QWidget()
        layout = QVBoxLayout()

        # UI language selection
        ui_group = QGroupBox("Язык интерфейса")
        ui_layout = QHBoxLayout()
        ui_layout.addWidget(QLabel("Интерфейс:"))
        self.ui_lang_combo = QComboBox()
        self.ui_lang_combo.addItems(["ru", "uk", "en", "es"])  # базовый набор
        ui_layout.addWidget(self.ui_lang_combo)
        ui_group.setLayout(ui_layout)

        # Speech (STT/TTS) language selection
        speech_group = QGroupBox("Речь (распознавание и озвучка)")
        speech_layout = QVBoxLayout()
        row = QHBoxLayout()
        row.addWidget(QLabel("Речь (STT/TTS):"))
        self.speech_lang_combo = QComboBox()
        self.speech_lang_combo.addItems(["ru", "uk", "en", "es"])  # поддерживаемые языки
        row.addWidget(self.speech_lang_combo)
        speech_layout.addLayout(row)

        self.download_models_btn = QPushButton("Скачать/обновить модели Vosk для выбранного языка")
        self.download_models_btn.setToolTip("Скачает Vosk-модель для распознавания речи выбранного языка")
        self.download_models_btn.clicked.connect(self.handle_download_models)
        speech_layout.addWidget(self.download_models_btn)
        speech_group.setLayout(speech_layout)

        layout.addWidget(ui_group)
        layout.addWidget(speech_group)
        layout.addStretch()

        tab.setLayout(layout)
        return tab

    def handle_download_models(self):
        """Download appropriate Vosk model zip for selected language and unpack to models/."""
        # Determine language and target directory
        lang = (
            self.speech_lang_combo.currentText()
            if hasattr(self, "speech_lang_combo")
            else str(self.config.get("language.speech", "ru") or "ru")
        )
        models_dir = Path(str(self.config.get("paths.models", "models") or "models"))
        models_dir.mkdir(parents=True, exist_ok=True)

        # Map of language -> (preferred small model, fallback big model)
        vosk_urls = {
            "ru": (
                "https://alphacephei.com/vosk/models/vosk-model-small-ru-0.22.zip",
                "https://alphacephei.com/vosk/models/vosk-model-ru-0.42.zip",
            ),
            "en": (
                "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip",
                "https://alphacephei.com/vosk/models/vosk-model-en-us-0.22.zip",
            ),
            "es": (
                "https://alphacephei.com/vosk/models/vosk-model-small-es-0.42.zip",
                "https://alphacephei.com/vosk/models/vosk-model-es-0.42.zip",
            ),
            "uk": (
                "https://alphacephei.com/vosk/models/vosk-model-small-uk-v3-small.zip",
                "https://alphacephei.com/vosk/models/vosk-model-uk-v3.zip",
            ),
        }

        try:
            small_url, big_url = vosk_urls.get(lang, vosk_urls["en"])
            extracted = self._download_and_extract_zip(small_url, models_dir)
            # Try to auto-assign model path based on extracted folder
            if extracted:
                self.model_path_edit.setText(str(extracted))
                self.config.set("stt.model_path", str(extracted))
            QMessageBox.information(self, "Модели Vosk", f"Модель для языка '{lang}' установлена.")
        except Exception as e_small:
            try:
                extracted = self._download_and_extract_zip(big_url, models_dir)
                if extracted:
                    self.model_path_edit.setText(str(extracted))
                    self.config.set("stt.model_path", str(extracted))
                QMessageBox.information(self, "Модели Vosk", f"Большая модель для языка '{lang}' установлена.")
            except Exception as e_big:
                QMessageBox.critical(
                    self,
                    "Ошибка загрузки",
                    f"Не удалось скачать модели для '{lang}'.\nМаленькая: {e_small}\nБольшая: {e_big}",
                )

    def _download_and_extract_zip(self, url: str, target_dir: Path) -> Path:
        import io
        import os
        import urllib.request
        import zipfile

        parent = self.parent()
        try:
            if parent and hasattr(parent, "logger"):
                parent.logger.info(f"Downloading Vosk model: {url}")  # type: ignore[attr-defined]
        except Exception:
            pass
        with urllib.request.urlopen(url) as resp:
            data = resp.read()
        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            # Determine top-level directory from zip contents
            top_dirs = set(p.split("/")[0] for p in zf.namelist() if "/" in p)
            zf.extractall(target_dir)
        extracted_dir = None
        for d in top_dirs:
            candidate = target_dir / d
            if candidate.exists() and candidate.is_dir():
                extracted_dir = candidate
                break
        if parent and hasattr(parent, "logger"):
            parent.logger.info(f"Extracted Vosk model to: {extracted_dir or target_dir}")  # type: ignore[attr-defined]
        return extracted_dir or target_dir

    def create_modules_tab(self):
        """Create modules settings tab"""
        tab = QWidget()
        layout = QVBoxLayout()

        # API Keys group
        api_group = QGroupBox("API Ключи")
        api_layout = QVBoxLayout()

        # Weather API
        weather_layout = QHBoxLayout()
        weather_layout.addWidget(QLabel("OpenWeather:"))
        self.weather_api_edit = QLineEdit()
        self.weather_api_edit.setEchoMode(QLineEdit.EchoMode.Password)
        weather_layout.addWidget(self.weather_api_edit)
        api_layout.addLayout(weather_layout)

        # News API
        news_layout = QHBoxLayout()
        news_layout.addWidget(QLabel("NewsAPI:"))
        self.news_api_edit = QLineEdit()
        self.news_api_edit.setEchoMode(QLineEdit.EchoMode.Password)
        news_layout.addWidget(self.news_api_edit)
        api_layout.addLayout(news_layout)

        # Google Search API
        search_api_layout = QHBoxLayout()
        search_api_layout.addWidget(QLabel("Google Search API:"))
        self.search_api_edit = QLineEdit()
        self.search_api_edit.setEchoMode(QLineEdit.EchoMode.Password)
        search_api_layout.addWidget(self.search_api_edit)
        api_layout.addLayout(search_api_layout)

        # Google Search Engine ID
        search_engine_layout = QHBoxLayout()
        search_engine_layout.addWidget(QLabel("ID поисковой системы (CX):"))
        self.search_engine_edit = QLineEdit()
        search_engine_layout.addWidget(self.search_engine_edit)
        api_layout.addLayout(search_engine_layout)

        api_group.setLayout(api_layout)

        # Module settings group
        modules_group = QGroupBox("Модули")
        modules_layout = QVBoxLayout()

        self.weather_enabled = QCheckBox("Модуль погоды")
        self.news_enabled = QCheckBox("Модуль новостей")
        self.calendar_enabled = QCheckBox("Модуль календаря")
        self.system_control_enabled = QCheckBox("Управление системой")
        self.voice_activation_enabled = QCheckBox("Голосовая активация")
        self.search_enabled = QCheckBox("Веб-поиск Google")

        modules_layout.addWidget(self.weather_enabled)
        modules_layout.addWidget(self.news_enabled)
        modules_layout.addWidget(self.calendar_enabled)
        modules_layout.addWidget(self.system_control_enabled)
        modules_layout.addWidget(self.voice_activation_enabled)
        modules_layout.addWidget(self.search_enabled)

        modules_group.setLayout(modules_layout)

        layout.addWidget(api_group)
        layout.addWidget(modules_group)
        layout.addStretch()

        tab.setLayout(layout)
        return tab

    def create_advanced_tab(self):
        """Create advanced settings tab (with scrollable content)"""
        from PyQt6.QtWidgets import QScrollArea

        tab = QWidget()
        outer_layout = QVBoxLayout()
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)

        # Inner widget with actual content
        content = QWidget()
        layout = QVBoxLayout()

        # Auto-Update group (новая секция)
        update_group = QGroupBox("🔄 Автообновления")
        update_layout = QVBoxLayout()

        # Enable auto-update checkbox
        self.auto_update_enabled = QCheckBox("Проверять обновления при запуске")
        self.auto_update_enabled.setToolTip("Автоматическая проверка новых версий на GitHub при старте приложения")
        update_layout.addWidget(self.auto_update_enabled)

        # Auto-install checkbox
        self.auto_install_updates = QCheckBox("Автоматически устанавливать обновления")
        self.auto_install_updates.setToolTip("Устанавливать обновления без запроса подтверждения (требует перезапуска)")
        update_layout.addWidget(self.auto_install_updates)

        # Manual check button
        self.check_updates_button = QPushButton("🔍 Проверить обновления сейчас")
        self.check_updates_button.setToolTip("Проверить наличие новой версии Arvis на GitHub")
        self.check_updates_button.clicked.connect(self.check_for_updates)
        update_layout.addWidget(self.check_updates_button)

        update_hint = QLabel("Обновления загружаются с GitHub и применяются с автоматическим созданием резервной копии.")
        update_hint.setWordWrap(True)
        update_hint.setStyleSheet("color: rgba(255, 255, 255, 0.6); background: transparent; font-size: 11px;")
        update_layout.addWidget(update_hint)

        update_group.setLayout(update_layout)

        # Logging group
        logging_group = QGroupBox("Логирование")
        logging_layout = QVBoxLayout()

        # Log level
        level_layout = QHBoxLayout()
        level_layout.addWidget(QLabel("Уровень логов:"))
        self.log_level_combo = QComboBox()
        self.log_level_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR"])
        self.log_level_combo.setCurrentText("INFO")
        level_layout.addWidget(self.log_level_combo)
        logging_layout.addLayout(level_layout)

        # Enable file logging
        self.file_logging_enabled = QCheckBox("Записывать логи в файл")
        logging_layout.addWidget(self.file_logging_enabled)

        logging_group.setLayout(logging_layout)

        # Ollama server group
        ollama_group = QGroupBox("Ollama сервер")
        ollama_layout = QVBoxLayout()

        mode_layout = QHBoxLayout()
        mode_layout.addWidget(QLabel("Режим запуска:"))
        self.ollama_mode_combo = QComboBox()
        self.ollama_mode_combo.addItem("Фоновый (без окна)", "background")
        self.ollama_mode_combo.addItem("Отдельное окно консоли", "console")
        self.ollama_mode_combo.addItem("Детач (фоновый с логами)", "detached")
        mode_layout.addWidget(self.ollama_mode_combo)
        mode_layout.addStretch()
        ollama_layout.addLayout(mode_layout)

        bind_layout = QHBoxLayout()
        bind_layout.addWidget(QLabel("Адрес привязки:"))
        self.ollama_bind_edit = QLineEdit()
        self.ollama_bind_edit.setPlaceholderText("127.0.0.1")
        bind_layout.addWidget(self.ollama_bind_edit)
        bind_layout.addStretch()
        ollama_layout.addLayout(bind_layout)

        self.ollama_external_checkbox = QCheckBox("Разрешить внешний доступ (0.0.0.0)")
        self.ollama_autorestart_checkbox = QCheckBox("Перезапускать при сбое")
        ollama_layout.addWidget(self.ollama_external_checkbox)
        ollama_layout.addWidget(self.ollama_autorestart_checkbox)

        ollama_hint = QLabel('В режиме "Консоль" открывается отдельное окно Windows, "Детач" пишет вывод в лог-файлы.')
        ollama_hint.setWordWrap(True)
        ollama_hint.setStyleSheet("color: rgba(255, 255, 255, 0.6); background: transparent; font-size: 11px;")
        ollama_layout.addWidget(ollama_hint)

        ollama_group.setLayout(ollama_layout)

        # Paths group
        paths_group = QGroupBox("Пути")
        paths_layout = QVBoxLayout()

        # Logs directory
        logs_layout = QHBoxLayout()
        logs_layout.addWidget(QLabel("Папка логов:"))
        self.logs_path_edit = QLineEdit()
        self.logs_browse_button = QPushButton("Обзор...")
        self.logs_browse_button.clicked.connect(self.browse_logs_path)
        logs_layout.addWidget(self.logs_path_edit)
        logs_layout.addWidget(self.logs_browse_button)
        paths_layout.addLayout(logs_layout)

        # Models directory
        models_layout = QHBoxLayout()
        models_layout.addWidget(QLabel("Папка моделей:"))
        self.models_path_edit = QLineEdit()
        self.models_browse_button = QPushButton("Обзор...")
        self.models_browse_button.clicked.connect(self.browse_models_path)
        models_layout.addWidget(self.models_path_edit)
        models_layout.addWidget(self.models_browse_button)
        paths_layout.addLayout(models_layout)

        paths_group.setLayout(paths_layout)

        # Log management group
        log_mgmt_group = QGroupBox("Управление логами")
        log_mgmt_layout = QVBoxLayout()

        self.clear_logs_button = QPushButton("Очистить старые логи")
        self.clear_logs_button.setToolTip("Удалить все логи, кроме текущей сессии")
        self.clear_logs_button.clicked.connect(self.clear_old_logs)
        log_mgmt_layout.addWidget(self.clear_logs_button)

        log_mgmt_group.setLayout(log_mgmt_layout)

        layout.addWidget(update_group)  # Добавляем секцию обновлений первой
        layout.addWidget(logging_group)
        layout.addWidget(ollama_group)
        layout.addWidget(paths_group)
        layout.addWidget(log_mgmt_group)
        layout.addStretch()

        content.setLayout(layout)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(content)
        # Match scrollbar styling with main chat scroll
        scroll.setStyleSheet(
            """
            QScrollArea { border: none; background-color: transparent; }
            QScrollBar:vertical { background-color: rgba(255,255,255,0.1); width: 8px; border-radius: 4px; }
            QScrollBar::handle:vertical { background-color: rgba(255,255,255,0.3); border-radius: 4px; min-height: 20px; }
            QScrollBar::handle:vertical:hover { background-color: rgba(255,255,255,0.5); }
            """
        )

        outer_layout.addWidget(scroll)
        tab.setLayout(outer_layout)
        return tab
    
    def check_for_updates(self):
        """Открыть диалог проверки обновлений"""
        try:
            from .update_dialog import UpdateDialog

            dialog = UpdateDialog(self)
            
            # Если обновление применено, перезапускаем приложение
            dialog.update_applied.connect(self.handle_update_applied)
            
            dialog.exec()

        except Exception as e:
            QMessageBox.critical(
                self,
                "Ошибка",
                f"Не удалось открыть диалог обновлений:\n{str(e)}",
            )

    def handle_update_applied(self):
        """Обработка применённого обновления"""
        # Перезапуск приложения
        self.accept()
        parent = self.parent()
        if parent and hasattr(parent, "restart_application"):
            parent.restart_application()

    def create_users_tab(self):
        """Create users management tab"""
        tab = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)

        # Authentication group
        auth_group = QGroupBox("🔐 Аутентификация")
        auth_layout = QVBoxLayout()

        # Enable authentication checkbox
        self.auth_enabled_checkbox = QCheckBox("Включить систему аутентификации")
        self.auth_enabled_checkbox.setToolTip("Включить систему входа с паролями и управление пользователями")
        auth_layout.addWidget(self.auth_enabled_checkbox)

        # 2FA settings
        self.twofa_enabled_checkbox = QCheckBox("Включить двухфакторную аутентификацию (2FA)")
        self.twofa_enabled_checkbox.setToolTip("Дополнительная защита с помощью одноразовых кодов (TOTP)")
        auth_layout.addWidget(self.twofa_enabled_checkbox)

        # Session timeout
        timeout_layout = QHBoxLayout()
        timeout_layout.addWidget(QLabel("Время сессии (минуты):"))
        self.session_timeout_spin = QSpinBox()
        self.session_timeout_spin.setRange(5, 1440)  # 5 min to 24 hours
        self.session_timeout_spin.setValue(60)
        self.session_timeout_spin.setToolTip("Автоматический выход после периода неактивности")
        timeout_layout.addWidget(self.session_timeout_spin)
        timeout_layout.addStretch()
        auth_layout.addLayout(timeout_layout)

        auth_group.setLayout(auth_layout)
        layout.addWidget(auth_group)

        # User Management group
        user_mgmt_group = QGroupBox("👥 Управление пользователями")
        user_mgmt_layout = QVBoxLayout()

        info_label = QLabel("Настройте пользователей, их роли и права доступа.\n" "Доступные роли: Admin, User, Guest")
        info_label.setStyleSheet("color: rgba(255, 255, 255, 0.7); background: transparent;")
        info_label.setWordWrap(True)
        user_mgmt_layout.addWidget(info_label)

        # Open user management button
        self.open_user_mgmt_button = QPushButton("🔧 Открыть управление пользователями")
        self.open_user_mgmt_button.setToolTip(
            "Открыть панель управления пользователями (требуются права администратора)"
        )
        self.open_user_mgmt_button.clicked.connect(self.open_user_management)
        user_mgmt_layout.addWidget(self.open_user_mgmt_button)

        user_mgmt_group.setLayout(user_mgmt_layout)
        layout.addWidget(user_mgmt_group)

        # Current User Info group (if authenticated)
        current_user_group = QGroupBox("👤 Текущий пользователь")
        current_user_layout = QVBoxLayout()

        self.current_user_label = QLabel("Не аутентифицирован")
        self.current_user_label.setStyleSheet("color: rgba(255, 255, 255, 0.8); background: transparent;")
        current_user_layout.addWidget(self.current_user_label)

        # Change password button
        self.change_password_button = QPushButton("🔑 Изменить пароль")
        self.change_password_button.clicked.connect(self.change_password)
        self.change_password_button.setEnabled(False)
        current_user_layout.addWidget(self.change_password_button)

        # Setup 2FA button
        self.setup_2fa_button = QPushButton("📱 Настроить 2FA")
        self.setup_2fa_button.clicked.connect(self.setup_2fa)
        self.setup_2fa_button.setEnabled(False)
        current_user_layout.addWidget(self.setup_2fa_button)

        current_user_group.setLayout(current_user_layout)
        layout.addWidget(current_user_group)

        # Security audit group
        security_group = QGroupBox("🛡️ Безопасность и аудит")
        security_layout = QVBoxLayout()

        self.audit_enabled_checkbox = QCheckBox("Включить журнал аудита")
        self.audit_enabled_checkbox.setToolTip("Записывать все действия пользователей в журнал")
        security_layout.addWidget(self.audit_enabled_checkbox)

        # View audit log button
        self.view_audit_button = QPushButton("📋 Просмотр журнала аудита")
        self.view_audit_button.clicked.connect(self.view_audit_log)
        security_layout.addWidget(self.view_audit_button)

        security_group.setLayout(security_layout)
        layout.addWidget(security_group)

        layout.addStretch()

        tab.setLayout(layout)
        return tab

    def open_user_management(self):
        """Open user management dialog"""
        try:
            from .user_management_dialog import UserManagementDialog

            # Check if authentication is enabled
            auth_enabled = bool(
                self.config.get("security.auth.enabled", self.config.get("security.auth_enabled", False))
            )
            if not auth_enabled:
                QMessageBox.information(
                    self,
                    "Аутентификация отключена",
                    "Включите систему аутентификации для управления пользователями.",
                )
                return

            # Get current user ID (from parent MainWindow if available)
            current_user_id = self.current_user_id
            if not current_user_id and self.parent():
                current_user_id = getattr(self.parent(), "current_user_id", None)

            if not current_user_id:
                QMessageBox.warning(
                    self,
                    "Необходима авторизация",
                    "Войдите в систему для управления пользователями.",
                )
                return

            # Open user management dialog
            dialog = UserManagementDialog(current_user_id, self)
            dialog.exec()

        except Exception as e:
            QMessageBox.critical(
                self,
                "Ошибка",
                f"Не удалось открыть управление пользователями:\n{str(e)}",
            )

    def change_password(self):
        """Change current user password"""
        try:
            from .change_password_dialog import ChangePasswordDialog

            dialog = ChangePasswordDialog(self.current_user_id, self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                QMessageBox.information(self, "Успех", "Пароль успешно изменён")
        except ImportError:
            QMessageBox.information(
                self,
                "В разработке",
                "Функция смены пароля будет доступна в следующей версии.",
            )

    def setup_2fa(self):
        """Setup 2FA for current user"""
        try:
            from .setup_2fa_dialog import Setup2FADialog

            dialog = Setup2FADialog(self.current_user_id, self)
            dialog.exec()
        except ImportError:
            QMessageBox.information(
                self,
                "В разработке",
                "Функция настройки 2FA будет доступна в следующей версии.",
            )

    def view_audit_log(self):
        """View audit log"""
        try:
            from .audit_log_dialog import AuditLogDialog

            dialog = AuditLogDialog(self)
            dialog.exec()
        except ImportError:
            QMessageBox.information(
                self,
                "В разработке",
                "Просмотр журнала аудита будет доступен в следующей версии.",
            )

    def load_settings(self):
        """Load settings from config"""
        # General tab
        self.name_edit.setText(str(self.config.get("user.name", "") or ""))
        self.city_edit.setText(str(self.config.get("user.city", "") or ""))

        # LLM tab
        self.ollama_url_edit.setText(str(self.config.get("llm.ollama_url", "") or ""))
        self.default_model_combo.setCurrentText(str(self.config.get("llm.default_model", "") or ""))

        temp_raw = self.config.get("llm.temperature", 0.7)
        try:
            temp_float = float(str(temp_raw))
        except Exception:
            temp_float = 0.7
        temp = int(temp_float * 100)
        self.temperature_slider.setValue(temp)
        self.temp_label.setText(f"{temp/100:.1f}")

        max_tokens_raw = self.config.get("llm.max_tokens", 2048)
        try:
            max_tokens_val = int(str(max_tokens_raw))
        except Exception:
            max_tokens_val = 2048
        self.max_tokens_spin.setValue(max_tokens_val)
        # Streaming mode
        use_stream = bool(self.config.get("llm.stream", True))
        simulate = bool(self.config.get("ui.simulate_streaming", True))
        if use_stream:
            self.stream_mode_combo.setCurrentIndex(0)
        elif simulate:
            self.stream_mode_combo.setCurrentIndex(1)
        else:
            self.stream_mode_combo.setCurrentIndex(2)

        # TTS/STT tab
        self.wake_word_edit.setText(str(self.config.get("stt.wake_word", "") or ""))
        self.model_path_edit.setText(str(self.config.get("stt.model_path", "") or ""))

        # Modules tab
        self.weather_api_edit.setText(str(self.config.get("weather.api_key", "") or ""))
        self.news_api_edit.setText(str(self.config.get("news.api_key", "") or ""))
        self.search_api_edit.setText(str(self.config.get("search.api_key", "") or ""))
        self.search_engine_edit.setText(str(self.config.get("search.engine_id", "") or ""))

        # Advanced tab
        self.logs_path_edit.setText(str(self.config.get("paths.logs", "") or ""))
        self.models_path_edit.setText(str(self.config.get("paths.models", "") or ""))
        if hasattr(self, "ollama_mode_combo"):
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
            idx = self.ollama_mode_combo.findData(launch_mode)
            if idx == -1:
                idx = 0
            self.ollama_mode_combo.setCurrentIndex(idx)

            allow_external = bool(self.config.get("security.ollama.allow_external", False))
            self.ollama_external_checkbox.setChecked(allow_external)
            bind_value = str(self.config.get("security.ollama.bind_address", "127.0.0.1") or "127.0.0.1")
            if not allow_external and bind_value == "0.0.0.0":
                bind_value = "127.0.0.1"
            self.ollama_bind_edit.setText(bind_value)
            self.ollama_autorestart_checkbox.setChecked(bool(self.config.get("security.ollama.auto_restart", True)))
        # Load startup options
        self.autostart_ollama.setChecked(bool(self.config.get("startup.autostart_ollama", False)))
        self.preload_model.setChecked(bool(self.config.get("startup.preload_model", False)))
        self.minimize_to_tray.setChecked(bool(self.config.get("startup.minimize_to_tray", False)))
        # Load app autostart
        self.autostart_app.setChecked(bool(self.config.get("startup.autostart_app", False)))
        # Load TTS settings
        # Выбираем движок и соответствующий ключ голоса, чтобы не подменять Bark голос Silero-значением
        try:
            current_engine = str(self.tts_engine_combo.currentData() or "silero").lower()
        except Exception:
            current_engine = "silero"
        if current_engine == "bark":
            voice_key = str(self.config.get("tts.bark.voice", "v2/en_speaker_0") or "v2/en_speaker_0")
        else:
            voice_key = str(self.config.get("tts.voice", "aidar") or "aidar")

        # Ищем точное соответствие по itemData, а не по тексту
        selected_idx = -1
        for i in range(self.voice_combo.count()):
            if self.voice_combo.itemData(i) == voice_key:
                selected_idx = i
                break
        if selected_idx >= 0:
            self.voice_combo.setCurrentIndex(selected_idx)
        else:
            # Фолбэк: для Silero пробуем aidar, для Bark — v2/en_speaker_0
            fallback_key = "v2/en_speaker_0" if current_engine == "bark" else "aidar"
            for i in range(self.voice_combo.count()):
                if self.voice_combo.itemData(i) == fallback_key:
                    self.voice_combo.setCurrentIndex(i)
                    break
        rate = str(self.config.get("tts.sample_rate", 48000) or 48000)
        idxr = self.sample_rate_combo.findText(rate)
        if idxr != -1:
            self.sample_rate_combo.setCurrentIndex(idxr)

        # Load TTS mode settings
        tts_mode = str(self.config.get("tts.mode", "realtime") or "realtime")
        if tts_mode == "realtime":
            self.tts_mode_combo.setCurrentIndex(0)
        elif tts_mode == "sentence_by_sentence":
            self.tts_mode_combo.setCurrentIndex(1)
        elif tts_mode == "after_complete":
            self.tts_mode_combo.setCurrentIndex(2)

        # Load TTS enable setting
        self.enable_tts_checkbox.setChecked(bool(self.config.get("tts.enabled", True)))
        # SAPI fallback option
        self.sapi_checkbox.setChecked(bool(self.config.get("tts.sapi_enabled", True)))
        # Load modules toggles
        self.weather_enabled.setChecked(bool(self.config.get("modules.weather_enabled", True)))
        self.news_enabled.setChecked(bool(self.config.get("modules.news_enabled", True)))
        self.calendar_enabled.setChecked(bool(self.config.get("modules.calendar_enabled", True)))
        self.system_control_enabled.setChecked(bool(self.config.get("modules.system_control_enabled", True)))
        self.voice_activation_enabled.setChecked(bool(self.config.get("modules.voice_activation_enabled", False)))
        self.search_enabled.setChecked(bool(self.config.get("search.enabled", True)))
        # Load logging settings
        self.log_level_combo.setCurrentText(str(self.config.get("logging.level", "INFO") or "INFO"))
        self.file_logging_enabled.setChecked(bool(self.config.get("logging.file_logging", True)))

        # Load users tab settings
        self.auth_enabled_checkbox.setChecked(bool(self.config.get("security.auth.enabled", False)))
        self.twofa_enabled_checkbox.setChecked(bool(self.config.get("security.auth.two_factor.enabled", False)))

        timeout_val = self.config.get("security.auth.session_timeout_minutes", 60)
        try:
            timeout_int = int(str(timeout_val))
        except Exception:
            timeout_int = 60
        self.session_timeout_spin.setValue(timeout_int)

        self.audit_enabled_checkbox.setChecked(bool(self.config.get("audit.enabled", True)))

        # Update current user info if available
        if self.current_user_id:
            try:
                from utils.security import get_auth_manager

                auth_manager = get_auth_manager()
                storage = getattr(auth_manager, "storage", None)
                user = storage.get_user_by_id(self.current_user_id) if storage else None
                if user:
                    self.current_user_label.setText(
                        f"Пользователь: {user.username}\nРоль: {user.role.value}\n"
                        f"2FA: {'Включен' if user.totp_secret else 'Отключен'}"
                    )
                    self.change_password_button.setEnabled(True)
                    self.setup_2fa_button.setEnabled(True)
            except Exception as e:
                self.current_user_label.setText(f"Ошибка загрузки данных: {e}")
        else:
            self.current_user_label.setText("Не аутентифицирован")
            self.change_password_button.setEnabled(False)
            self.setup_2fa_button.setEnabled(False)
        # Language tab
        if hasattr(self, "ui_lang_combo"):
            self.ui_lang_combo.setCurrentText(str(self.config.get("language.ui", "ru") or "ru"))
        if hasattr(self, "speech_lang_combo"):
            self.speech_lang_combo.setCurrentText(str(self.config.get("language.speech", "ru") or "ru"))
        
        # Auto-update settings
        if hasattr(self, "auto_update_enabled"):
            self.auto_update_enabled.setChecked(bool(self.config.get("auto_update.check_on_startup", True)))
        if hasattr(self, "auto_install_updates"):
            self.auto_install_updates.setChecked(bool(self.config.get("auto_update.auto_install", False)))

    def save_settings(self):
        """Save settings and close dialog"""
        self.apply_settings()
        self.accept()

    def apply_settings(self, silent: bool = False):
        """Apply current settings. If silent=True, do not show message box."""
        # General tab
        self.config.set("user.name", self.name_edit.text())
        self.config.set("user.city", self.city_edit.text())

        # LLM tab
        self.config.set("llm.ollama_url", self.ollama_url_edit.text())
        self.config.set("llm.default_model", self.default_model_combo.currentText())
        self.config.set("llm.temperature", self.temperature_slider.value() / 100.0)
        self.config.set("llm.max_tokens", self.max_tokens_spin.value())
        # Streaming mode mapping
        mode_idx = self.stream_mode_combo.currentIndex()
        if mode_idx == 0:  # Real streaming
            self.config.set("llm.stream", True)
            self.config.set("ui.simulate_streaming", False)
        elif mode_idx == 1:  # Simulation
            self.config.set("llm.stream", False)
            self.config.set("ui.simulate_streaming", True)
        else:  # Off
            self.config.set("llm.stream", False)
            self.config.set("ui.simulate_streaming", False)

        # TTS/STT tab
        # Save TTS selection
        # Extract raw voice key from combo text (before space if present)
        voice_text = self.voice_combo.currentText()
        voice_key = voice_text.split(" ")[0]
        # Save selected engine and voice
        try:
            selected_engine = str(self.tts_engine_combo.currentData() or "silero")
        except Exception:
            selected_engine = "silero"
        self.config.set("tts.default_engine", selected_engine)
        # Voice key from item data (fallback to parsed text)
        voice_key = self.voice_combo.currentData() or self.voice_combo.currentText().split(" ")[0]
        if selected_engine == "silero":
            self.config.set("tts.voice", str(voice_key))
        else:
            self.config.set("tts.bark.voice", str(voice_key))
        self.config.set("tts.sample_rate", int(self.sample_rate_combo.currentText()))
        self.config.set("tts.enabled", self.enable_tts_checkbox.isChecked())
        self.config.set("tts.sapi_enabled", self.sapi_checkbox.isChecked())

        # Save TTS mode
        tts_mode_idx = self.tts_mode_combo.currentIndex()
        if tts_mode_idx == 0:
            self.config.set("tts.mode", "realtime")
        elif tts_mode_idx == 1:
            self.config.set("tts.mode", "sentence_by_sentence")
        elif tts_mode_idx == 2:
            self.config.set("tts.mode", "after_complete")

        self.config.set("stt.wake_word", self.wake_word_edit.text())
        self.config.set("stt.model_path", self.model_path_edit.text())

        # Modules tab
        self.config.set("weather.api_key", self.weather_api_edit.text())
        self.config.set("news.api_key", self.news_api_edit.text())
        self.config.set("search.api_key", self.search_api_edit.text())
        self.config.set("search.engine_id", self.search_engine_edit.text())
        # Save module toggles
        self.config.set("modules.weather_enabled", self.weather_enabled.isChecked())
        self.config.set("modules.news_enabled", self.news_enabled.isChecked())
        self.config.set("modules.calendar_enabled", self.calendar_enabled.isChecked())
        self.config.set("modules.system_control_enabled", self.system_control_enabled.isChecked())
        self.config.set("modules.voice_activation_enabled", self.voice_activation_enabled.isChecked())
        self.config.set("search.enabled", self.search_enabled.isChecked())

        # Advanced tab
        self.config.set("paths.logs", self.logs_path_edit.text())
        self.config.set("paths.models", self.models_path_edit.text())
        self.config.set("logging.level", self.log_level_combo.currentText())
        self.config.set("logging.file_logging", self.file_logging_enabled.isChecked())
        if hasattr(self, "ollama_mode_combo"):
            mode_value = self.ollama_mode_combo.currentData()
            if mode_value:
                mode_str = str(mode_value)
                self.config.set("security.ollama.launch_mode", mode_str)
                self.config.set("startup.ollama_launch_mode", mode_str)

            allow_external = self.ollama_external_checkbox.isChecked()
            bind_value = self.ollama_bind_edit.text().strip()
            if not bind_value:
                bind_value = "0.0.0.0" if allow_external else "127.0.0.1"
            elif allow_external and bind_value == "127.0.0.1":
                bind_value = "0.0.0.0"

            self.config.set("security.ollama.bind_address", bind_value)
            self.config.set("security.ollama.allow_external", allow_external)
            self.config.set("security.ollama.auto_restart", self.ollama_autorestart_checkbox.isChecked())
        # Language tab
        if hasattr(self, "ui_lang_combo"):
            self.config.set("language.ui", self.ui_lang_combo.currentText())
        if hasattr(self, "speech_lang_combo"):
            self.config.set("language.speech", self.speech_lang_combo.currentText())

        # Startup options
        self.config.set("startup.autostart_ollama", self.autostart_ollama.isChecked())
        self.config.set("startup.preload_model", self.preload_model.isChecked())
        self.config.set("startup.minimize_to_tray", self.minimize_to_tray.isChecked())
        # Save app autostart and apply to Windows registry (no-op on non-Windows)
        self.config.set("startup.autostart_app", self.autostart_app.isChecked())
        try:
            self._apply_windows_autostart(self.autostart_app.isChecked())
        except Exception:
            pass

        # Users tab
        self.config.set("security.auth.enabled", self.auth_enabled_checkbox.isChecked())
        self.config.set("security.auth.two_factor.enabled", self.twofa_enabled_checkbox.isChecked())
        self.config.set("security.auth.session_timeout_minutes", self.session_timeout_spin.value())
        self.config.set("audit.enabled", self.audit_enabled_checkbox.isChecked())

        # Auto-update settings
        if hasattr(self, "auto_update_enabled"):
            self.config.set("auto_update.check_on_startup", self.auto_update_enabled.isChecked())
        if hasattr(self, "auto_install_updates"):
            self.config.set("auto_update.auto_install", self.auto_install_updates.isChecked())

        # Save config to disk
        try:
            self.config.save_config()
        except Exception as e:
            # В диалоге нет собственного логгера — выводим в консоль
            print(f"Failed to save config: {e}")

        # Emit settings changed signal
        self.settings_changed.emit(self.config.config_data)

        if not silent:
            QMessageBox.information(self, "Настройки", "Настройки сохранены успешно!")

    def _apply_windows_autostart(self, enable: bool):
        """Включает/выключает автозапуск приложения через реестр Windows (HKCU\\...\\Run)."""
        import os
        import sys
        from pathlib import Path

        if os.name != "nt":
            return  # Только для Windows
        try:
            import winreg
        except Exception:
            return  # winreg может быть недоступен в среде

        # Предпочтительно запускать через start_arvis.bat, если он есть
        # Иначе — через текущий интерпретатор Python и главный скрипт
        workspace_root = Path.cwd()
        bat_path = workspace_root / "start_arvis.bat"
        if bat_path.exists():
            command = f'"{str(bat_path)}"'
        else:
            exe = sys.executable
            script = Path(sys.argv[0]).resolve()
            command = f'"{exe}" "{str(script)}"'

        run_key_path = r"Software\\Microsoft\\Windows\\CurrentVersion\\Run"
        app_name = "Arvis"
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, run_key_path, 0, winreg.KEY_ALL_ACCESS) as key:
            if enable:
                winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, command)
            else:
                try:
                    winreg.DeleteValue(key, app_name)
                except FileNotFoundError:
                    pass

    def clear_old_logs(self):
        """Clear all old log files except current session with confirmation"""
        import glob
        import os
        from pathlib import Path

        from PyQt6.QtWidgets import QMessageBox

        # Confirm action
        reply = QMessageBox.question(
            self,
            "Очистка логов",
            "Удалить все старые логи, кроме текущей сессии?\n\nЭто действие необратимо.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            logs_dir = Path(str(self.config.get("paths.logs", "logs") or "logs"))
            if not logs_dir.exists():
                QMessageBox.information(self, "Очистка логов", "Папка логов не найдена.")
                return

            # Get current session log pattern (today's date + session ID)
            import datetime

            today = datetime.datetime.now().strftime("%Y%m%d")
            current_session_pattern = f"arvis_{today}_*_*.log"

            # Find all log files
            all_logs = list(logs_dir.glob("*.log"))
            current_session_logs = list(logs_dir.glob(current_session_pattern))

            # Files to delete = all logs - current session logs
            files_to_delete = [f for f in all_logs if f not in current_session_logs]

            deleted_count = 0
            for log_file in files_to_delete:
                try:
                    log_file.unlink()
                    deleted_count += 1
                except Exception as e:
                    print(f"Failed to delete {log_file}: {e}")

            QMessageBox.information(
                self, "Очистка логов", f"Удалено файлов логов: {deleted_count}\nТекущая сессия сохранена."
            )

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось очистить логи:\n{e}")

    def browse_model_path(self):
        """Browse for Vosk model directory"""
        path = QFileDialog.getExistingDirectory(self, "Выберите папку с моделью Vosk")
        if path:
            self.model_path_edit.setText(path)

    def browse_logs_path(self):
        """Browse for logs directory"""
        path = QFileDialog.getExistingDirectory(self, "Выберите папку для логов")
        if path:
            self.logs_path_edit.setText(path)

    def browse_models_path(self):
        """Browse for models directory"""
        path = QFileDialog.getExistingDirectory(self, "Выберите папку для моделей")
        if path:
            self.models_path_edit.setText(path)
