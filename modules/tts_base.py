"""
Base class for TTS engines
Базовый класс для всех TTS engine'ов с абстрактными методами
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Callable, Dict, Any, Optional
from dataclasses import dataclass


class TTSStatus(Enum):
    """Статус TTS engine"""
    IDLE = "idle"
    INITIALIZING = "initializing"
    READY = "ready"
    SPEAKING = "speaking"
    ERROR = "error"


@dataclass
class HealthCheckResult:
    """Результат health check"""
    healthy: bool
    message: str
    details: Optional[Dict[str, Any]] = None


class TTSEngineBase(ABC):
    """
    Абстрактный базовый класс для всех TTS engine'ов.
    
    Все TTS engine'ы должны наследоваться от этого класса и реализовать
    методы speak(), speak_streaming(), stop(), get_status()
    """
    
    def __init__(self, config, logger):
        """
        Инициализация TTS engine.
        
        Args:
            config: Config объект
            logger: Logger экземпляр
        """
        self.config = config
        self.logger = logger
        self.status = TTSStatus.IDLE
        self.engine_name = "base"
    
    @abstractmethod
    def speak(self, text: str, stream: bool = False) -> bool:
        """
        Синтезировать и воспроизвести текст.
        
        Args:
            text: Текст для синтеза
            stream: Если True, стриминг аудио в реальном времени
        
        Returns:
            True если успешно, False в противном случае
        """
        pass
    
    @abstractmethod
    def speak_streaming(self, text: str, chunk_callback: Callable[[bytes], None]) -> bool:
        """
        Потоковый синтез с callback'ом для аудио чанков.
        
        Args:
            text: Текст для синтеза
            chunk_callback: Функция, вызываемая с каждым аудио чанком (PCM bytes)
        
        Returns:
            True если успешно, False в противном случае
        """
        pass
    
    @abstractmethod
    def stop(self) -> None:
        """Остановить воспроизведение"""
        pass
    
    def get_status(self) -> Dict[str, Any]:
        """
        Получить статус engine'а.
        
        Returns:
            Dict с engine, status, ready полями
        """
        return {
            "engine": self.engine_name,
            "status": self.status.value,
            "ready": self.status == TTSStatus.READY
        }
    
    def health_check(self) -> HealthCheckResult:
        """
        Проверка здоровья engine'а.
        
        Returns:
            HealthCheckResult с healthy, message, details
        """
        is_healthy = self.status in [TTSStatus.READY, TTSStatus.SPEAKING]
        return HealthCheckResult(
            healthy=is_healthy,
            message=f"TTS engine status: {self.status.value}",
            details=self.get_status()
        )
