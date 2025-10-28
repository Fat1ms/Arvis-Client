"""
Arvis - AI Assistant Application
Main entry point for the application
"""

import asyncio
import logging
import os
import sys
import time
from pathlib import Path
from typing import Optional

from PyQt6.QtCore import Qt, QThread, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QFontDatabase, QPixmap
from PyQt6.QtWidgets import QApplication, QLabel, QProgressBar, QSplashScreen, QVBoxLayout, QWidget

from config.config import Config
from i18n import I18N
from i18n.i18n import apply_to_widget_tree
from src.gui.main_window import MainWindow
from src.gui.splash_screen import SplashScreen
from utils.logger import setup_logger
from version import get_app_name, get_version


class ArvisApp:
    def __init__(self):
        self.app = None
        self.main_window = None
        self.loading_screen = None
        self.config = Config()
        self.logger = setup_logger(config=self.config)
        # Данные пользователя после логина
        self.user_id = None
        self.username = None
        self.user_role = None

    def init_app(self):
        """Initialize the Qt application"""
        self.app = QApplication(sys.argv)
        self.app.setApplicationName(get_app_name())
        self.app.setApplicationVersion(get_version())
        # Init i18n language from config
        try:
            ui_lang = str(self.config.get("language.ui", "ru") or "ru")
            I18N.get().set_language(ui_lang)
        except Exception:
            pass

        # Load custom font
        self.load_fonts()

        # Set dark theme
        self.set_dark_theme()

    def load_fonts(self):
        """Load custom fonts: Exo 2 as default for all languages; KyivTypeSans as fallback"""
        loaded_families = []
        # Load Exo 2 variable fonts (regular + italic), then KyivTypeSans as fallback
        font_files = [
            Path("UXUI/Exo2-VariableFont_wght.ttf"),
            Path("UXUI/Exo2-Italic-VariableFont_wght.ttf"),
        ]

        for path in font_files:
            if path.exists():
                font_id = QFontDatabase.addApplicationFont(str(path))
                if font_id != -1:
                    families = QFontDatabase.applicationFontFamilies(font_id)
                    loaded_families.extend(families)
                    self.logger.info(f"Loaded font file '{path.name}' with families: {', '.join(families)}")
                else:
                    self.logger.warning(f"Failed to load font file: {path}")
            else:
                self.logger.warning(f"Font file not found: {path}")

        # Choose Exo 2 as base application font if available
        base_family = None
        for fam in loaded_families:
            if fam.lower().startswith("exo 2"):
                base_family = fam
                break
        if not base_family:
            # Fallback to KyivTypeSans if Exo 2 is not available
            for fam in loaded_families:
                if "kyivtype" in fam.lower():
                    base_family = fam
                    break
        if not base_family and loaded_families:
            base_family = loaded_families[0]

        if base_family and self.app is not None:
            self.app.setFont(QFont(base_family, 10))
            self.logger.info(f"Application base font set to: {base_family}")
        else:
            self.logger.warning("No custom fonts loaded; using system default font")

    def set_dark_theme(self):
        """Set dark theme for the application"""
        dark_stylesheet = """
        QWidget {
            background-color: rgb(43, 43, 43);
            color: white;
            /* Exo 2 as the default font across languages, with fallbacks */
            font-family: 'Exo 2', 'KyivType Sans', 'KyivTypeSans-VarGX', Arial, sans-serif;
        }

        QMainWindow {
            background-color: rgb(43, 43, 43);
        }

        QScrollArea {
            background-color: rgb(43, 43, 43);
            border: none;
        }

        QLineEdit {
            background-color: rgb(60, 60, 60);
            border: 1px solid rgb(80, 80, 80);
            border-radius: 5px;
            padding: 8px;
            color: white;
        }

        QPushButton {
            background-color: rgb(60, 60, 60);
            border: 1px solid rgb(80, 80, 80);
            border-radius: 5px;
            padding: 8px;
            color: white;
        }

        QPushButton:hover {
            background-color: rgb(80, 80, 80);
        }

        QPushButton:pressed {
            background-color: rgb(100, 100, 100);
        }

        QLabel {
            color: white;
        }

        QTextEdit {
            background-color: rgb(50, 50, 50);
            border: 1px solid rgb(70, 70, 70);
            color: white;
        }
        """
        if self.app is not None:
            self.app.setStyleSheet(dark_stylesheet)

    def show_login_dialog(self) -> bool:
        """Show login dialog and return True if login successful"""
        try:
            from PyQt6.QtWidgets import QDialog

            from src.gui.enhanced_login_dialog import EnhancedLoginDialog

            login_dialog = EnhancedLoginDialog()
            result = login_dialog.exec()

            if result == QDialog.DialogCode.Accepted:
                user_id, username, role = login_dialog.get_credentials()
                self.logger.info(f"Успешный вход: {username} (роль: {role})")
                # Сохраняем данные пользователя для передачи в main_window
                self.user_id = user_id
                self.username = username
                self.user_role = role
                return True
            else:
                return False

        except Exception as e:
            self.logger.error(f"Ошибка диалога входа: {e}")
            return False

    def show_loading_screen(self):
        """Show loading screen and initialize components"""
        try:
            from src.gui.loading_screen import LoadingScreen

            self.loading_screen = LoadingScreen()
            self.loading_screen.show()

            if self.app is not None:
                self.app.processEvents()

            # Запускаем загрузку компонентов
            QTimer.singleShot(100, self.load_components)

        except Exception as e:
            self.logger.error(f"Ошибка loading screen: {e}")

    def load_components(self):
        """Load all heavy components with progress updates"""
        try:
            if not hasattr(self, "loading_screen") or not self.main_window:
                return

            # Шаг 1: Инициализация базовых компонентов (10%)
            self.loading_screen.set_status("Инициализация базовых компонентов...", 10, "Настройка конфигурации")
            if self.app:
                self.app.processEvents()
            time.sleep(0.2)

            # Шаг 2: Запуск Ollama если нужно (20%)
            self.loading_screen.set_status("Проверка Ollama...", 20, "Подключение к LLM серверу")
            if self.app:
                self.app.processEvents()

            # Запускаем Ollama если autostart включён
            if self.config.get("startup.autostart_ollama", False):
                try:
                    self.main_window.start_ollama_if_needed()
                except Exception as e:
                    self.logger.warning(f"Ollama autostart failed: {e}")
            time.sleep(0.3)

            # Шаг 3: Инициализация ArvisCore (30-60%)
            # ArvisCore инициализирует STT, TTS, LLM и модули
            def progress_update(message, progress_val):
                """Callback для обновления прогресса"""
                try:
                    self.loading_screen.set_status(message, progress_val)
                    if self.app:
                        self.app.processEvents()
                except Exception:
                    pass

            progress_update("Загрузка модели распознавания речи...", 30)
            progress_update("Vosk STT (может занять несколько минут)...", 35)

            # Инициализируем ArvisCore с прогрессом
            if self.main_window.init_arvis_core_with_progress(lambda msg, prog: progress_update(msg, prog)):
                self.logger.info("ArvisCore инициализирован успешно")
            else:
                self.logger.warning("ArvisCore инициализация завершена с предупреждениями")

            # Шаг 4: Генерация фраз для wake word (80%)
            progress_update("Подготовка голосовых ответов...", 80)
            time.sleep(0.5)

            # Шаг 5: Прогрев LLM (90%)
            progress_update("Прогрев языковой модели...", 90)

            # Запускаем прогрев LLM
            try:
                if self.main_window and self.main_window.arvis_core:
                    self.main_window.warmup_llm()
            except Exception as e:
                self.logger.warning(f"LLM warmup failed: {e}")

            time.sleep(1.0)

            # Шаг 6: Завершение (100%)
            progress_update("Загрузка завершена!", 100)

            # Закрываем loading screen и показываем главное окно
            QTimer.singleShot(500, self.show_main_window)

        except Exception as e:
            self.logger.error(f"Ошибка загрузки компонентов: {e}")
            import traceback

            traceback.print_exc()
            if hasattr(self, "loading_screen"):
                try:
                    self.loading_screen.close()
                except Exception:
                    pass
            self.show_main_window()

    def show_main_window(self):
        """Show main window after loading complete"""
        try:
            if hasattr(self, "loading_screen"):
                self.loading_screen.close()
                self.loading_screen = None

            if self.main_window:
                # Передаём данные пользователя
                if hasattr(self, "user_id"):
                    self.main_window.handle_login_success(self.user_id, self.username, self.user_role)
                    # Устанавливаем роль для адаптации UI (показ кнопки управления пользователями для админов)
                    if hasattr(self.main_window, "set_user_role"):
                        self.main_window.set_user_role(self.user_role)

                self.main_window.show()
                self.main_window.raise_()
                self.main_window.activateWindow()
                self.logger.info("Главное окно отображено")

        except Exception as e:
            self.logger.error(f"Ошибка показа главного окна: {e}")

    def run(self):
        """Main run method"""
        try:
            self.logger.info("=== Запуск Arvis AI Assistant ===")

            # Базовая инициализация (шрифты, тема)
            self.init_app()

            # Показываем логин БЕЗ предварительной загрузки компонентов
            self.logger.info("Показ диалога входа...")
            if not self.show_login_dialog():
                self.logger.info("Вход отменён пользователем")
                return 0

            # После успешного логина показываем loading screen
            self.logger.info("Запуск загрузки компонентов...")
            self.show_loading_screen()

            # Initialize main window
            self.logger.info("Создание главного окна...")
            self.main_window = MainWindow(self.config)

            # Apply i18n to the whole widget tree after creation
            try:
                apply_to_widget_tree(self.main_window)
            except Exception as e:
                self.logger.warning(f"i18n apply failed: {e}")

            self.logger.info("GUI инициализирован. Запуск цикла событий...")

            # Start the event loop
            result = self.app.exec() if self.app is not None else 1

            # Временно отключаем мониторинг производительности
            # performance_monitor.stop_monitoring()
            #
            # # Показываем отчёт о производительности
            # report = performance_monitor.get_performance_report()
            # self.logger.info(f"Performance report: uptime={report['uptime']:.1f}s, "
            #                f"avg_cpu={report['avg_cpu']:.1f}%, "
            #                f"avg_memory={report['avg_memory']:.1f}%")

            return result

        except Exception as e:
            self.logger.error(f"Ошибка запуска приложения: {e}")
            import traceback

            traceback.print_exc()

            # Показываем сообщение об ошибке пользователю
            if hasattr(self, "app") and self.app:
                from PyQt6.QtWidgets import QMessageBox

                QMessageBox.critical(None, "Критическая ошибка", f"Ошибка запуска Arvis:\n{e}")
            return 1

    def ensure_main_window_visible(self):
        """Safety guard to force-show the main window on screen."""
        try:
            if not self.main_window:
                return
            # Если окно по какой-то причине не видно — показать и активировать
            if not self.main_window.isVisible():
                self.main_window.show()
            self.main_window.showNormal()
            try:
                if self.app is not None:
                    # Центрируем на доступной геометрии
                    screen = self.app.primaryScreen()
                    if screen is not None:
                        if hasattr(screen, "availableGeometry"):
                            geom = screen.availableGeometry()
                        else:
                            geom = screen.geometry()
                        frame = self.main_window.frameGeometry()
                        frame.moveCenter(geom.center())
                        self.main_window.move(frame.topLeft())
            except Exception:
                pass
            try:
                self.main_window.raise_()
                self.main_window.activateWindow()
            except Exception:
                pass
        except Exception as e:
            self.logger.warning(f"ensure_main_window_visible failed: {e}")


def main():
    """Main entry point"""
    # Set up logging
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    try:
        print("🚀 Запуск Arvis AI Assistant...")
        print("📱 GUI версия с исправлениями")
    except UnicodeEncodeError:
        print("Запуск Arvis AI Assistant...")
        print("GUI версия с исправлениями")
    print("=" * 50)

    app = ArvisApp()
    result = app.run()

    print(f"\n✅ Arvis завершён с кодом: {result}")
    return result


if __name__ == "__main__":
    sys.exit(main())
