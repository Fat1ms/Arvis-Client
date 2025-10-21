"""
TTS Factory for creating and managing TTS engines
Фабрика для создания и управления TTS engine'ами
"""

from typing import Optional, List, Type, Dict, Any
from modules.tts_base import TTSEngineBase
from utils.logger import ModuleLogger


class TTSFactory:
    """
    Фабрика для создания TTS engine'ов по имени.
    
    Поддерживает динамическую регистрацию engine'ов и их выбор в runtime.
    """
    
    # Реестр доступных engine'ов: имя -> класс
    _engines: Dict[str, Type[TTSEngineBase]] = {}
    _logger = ModuleLogger("TTSFactory")
    
    @classmethod
    def register_engine(cls, name: str, engine_class: Type[TTSEngineBase]) -> None:
        """
        Зарегистрировать новый TTS engine.
        
        Args:
            name: Имя engine'а (например, 'silero', 'bark', 'sapi')
            engine_class: Класс, наследующийся от TTSEngineBase
        
        Raises:
            TypeError: Если engine_class не наследуется от TTSEngineBase
        """
        if not issubclass(engine_class, TTSEngineBase):
            raise TypeError(f"{engine_class} must inherit from TTSEngineBase")
        
        cls._engines[name] = engine_class
        cls._logger.debug(f"Registered TTS engine: {name}")
    
    @classmethod
    def create_engine(
        cls, engine_name: str, config, logger
    ) -> Optional[TTSEngineBase]:
        """
        Создать TTS engine по имени.
        
        Args:
            engine_name: Имя engine'а (silero, bark, sapi)
            config: Config объект
            logger: Logger экземпляр
        
        Returns:
            TTSEngineBase экземпляр или None если не найден
        
        Raises:
            ValueError: Если engine не найден
            Exception: Если ошибка при создании engine'а
        """
        if engine_name not in cls._engines:
            available = list(cls._engines.keys())
            raise ValueError(
                f"Unknown TTS engine: {engine_name}. "
                f"Available engines: {available}"
            )
        
        engine_class = cls._engines[engine_name]
        try:
            instance = engine_class(config, logger)
            cls._logger.info(f"Created TTS engine: {engine_name}")
            return instance
        except Exception as e:
            cls._logger.error(f"Failed to create TTS engine {engine_name}: {e}")
            raise
    
    @classmethod
    def list_available_engines(cls) -> List[str]:
        """
        Получить список доступных TTS engine'ов.
        
        Returns:
            List имен доступных engine'ов
        """
        return list(cls._engines.keys())
    
    @classmethod
    def get_engine_info(cls, engine_name: str) -> Dict[str, Any]:
        """
        Получить информацию о TTS engine'е.
        
        Args:
            engine_name: Имя engine'а
        
        Returns:
            Dict с информацией об engine'е (name, class, module)
        """
        if engine_name not in cls._engines:
            return {}
        
        engine_class = cls._engines[engine_name]
        return {
            "name": engine_name,
            "class": engine_class.__name__,
            "module": engine_class.__module__,
        }
    
    @classmethod
    def is_engine_available(cls, engine_name: str) -> bool:
        """
        Проверить доступность engine'а.
        
        Args:
            engine_name: Имя engine'а
        
        Returns:
            True если engine доступен, False иначе
        """
        return engine_name in cls._engines


# ==============================================================================
# Auto-registration of built-in engines
# ==============================================================================

def _register_builtin_engines() -> None:
    """Зарегистрировать встроенные TTS engine'ы"""
    
    # Silero TTS (всегда доступна)
    try:
        from modules.silero_tts_engine import SileroTTSEngine
        TTSFactory.register_engine("silero", SileroTTSEngine)
    except ImportError as e:
        TTSFactory._logger.warning(f"Could not import SileroTTSEngine: {e}")
    except Exception as e:
        TTSFactory._logger.warning(f"Error registering SileroTTSEngine: {e}")
    
    # Bark TTS (опционально)
    try:
        from modules.bark_tts_engine import BarkTTSEngine
        TTSFactory.register_engine("bark", BarkTTSEngine)
    except ImportError:
        TTSFactory._logger.debug("BarkTTSEngine not available (optional)")
    except Exception as e:
        TTSFactory._logger.warning(f"Error registering BarkTTSEngine: {e}")
    
    # SAPI TTS (Windows only, опционально)
    try:
        from modules.system_tts import SAPITTSEngine
        TTSFactory.register_engine("sapi", SAPITTSEngine)
    except ImportError:
        TTSFactory._logger.debug("SAPITTSEngine not available (Windows only)")
    except Exception as e:
        TTSFactory._logger.warning(f"Error registering SAPITTSEngine: {e}")


# Вызвать при импорте модуля
_register_builtin_engines()
