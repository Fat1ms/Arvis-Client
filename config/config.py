"""
Configuration management for Arvis
"""

import copy
import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

from utils.env_loader import EnvLoader


class Config:
    def __init__(self, config_file: str = "config/config.json"):
        self.config_file = Path(config_file)
        self.env_loader = EnvLoader()
        self.config_data = self.load_config()

    def load_config(self) -> Dict[str, Any]:
        """Load configuration from file"""
        # Load from environment variables first, then config file
        api_keys = self.env_loader.get_api_keys()
        user_settings = self.env_loader.get_user_settings()
        llm_settings = self.env_loader.get_llm_settings()
        tts_settings = self.env_loader.get_tts_settings()
        stt_settings = self.env_loader.get_stt_settings()
        paths = self.env_loader.get_paths()
        search_settings = self.env_loader.get_search_settings()

        from version import get_app_name, get_version

        default_config = {
            "app": {"name": get_app_name(), "version": get_version(), "debug": self.env_loader.is_debug_mode()},
            "startup": {
                "autostart_ollama": False,
                "preload_model": False,
                "minimize_to_tray": False,
                "autostart_app": False,
                "ollama_launch_mode": "background",
            },
            "llm": {
                "default_model": llm_settings["default_model"],
                "ollama_url": llm_settings["ollama_url"],
                "temperature": llm_settings["temperature"],
                "max_tokens": llm_settings["max_tokens"],
                "stream": True,
            },
            "tts": {
                "engine": "silero",
                "voice": tts_settings["voice"],
                "sample_rate": tts_settings["sample_rate"],
                "device": tts_settings["device"],
                "enabled": True,
                "mode": "realtime",
                "sapi_enabled": False,
            },
            "stt": {
                "engine": "vosk",
                "model_path": stt_settings["model_path"],
                "wake_word": stt_settings["wake_word"],
            },
            "modules": {
                "weather_enabled": True,
                "news_enabled": True,
                "calendar_enabled": True,
                "system_control_enabled": True,
                "voice_activation_enabled": False,
            },
            "weather": {
                "api_key": api_keys["weather"],
                "api_url": "http://api.openweathermap.org/data/2.5/weather",
                "default_city": user_settings["city"],
            },
            "news": {
                "api_key": api_keys["news"],
                "api_url": "https://newsapi.org/v2/top-headlines",
                "country": "ua",
                "language": "ru",
            },
            "user": {"name": user_settings["name"], "city": user_settings["city"]},
            "audio": {"input_device": None, "output_device": None, "volume": 0.8},
            "ui": {"simulate_streaming": True, "stream_interval_ms": 16, "stream_chunk": 2},
            "history": {
                "max_messages": 50,
                "save_to_file": True,
                "auto_save_interval": 5,
            },
            "logging": {
                "level": "INFO",
                "console_level": "INFO",
                "file_level": "DEBUG",
                "file_logging": True,
                "mode": "session",
                "rotation": "size",
                "max_bytes": 5 * 1024 * 1024,
                "backup_count": 7,
            },
            "language": {"ui": "ru", "speech": "ru"},
            "paths": {
                "logs": paths["logs"],
                "models": paths["models"],
                "temp": paths["temp"],
                "data": paths["data"],
            },
            "search": {
                "enabled": bool(search_settings.get("enabled", True)),
                "api_key": api_keys.get("search", ""),
                "engine_id": search_settings.get("engine_id", ""),
                "results_limit": 3,
                "region": "ru",
            },
            "security": {
                "auth": {
                    "enabled": True,
                    "require_login": False,
                    "use_remote_server": False,
                    "server_url": "http://127.0.0.1:8000",
                    "fallback_to_local": True,
                    "auto_login_guest_on_failure": False,
                    "session_timeout_minutes": 60,
                    "password_policy": {
                        "min_length": 8,
                        "require_uppercase": True,
                        "require_lowercase": True,
                        "require_digit": True,
                        "require_special": True,
                    },
                    "lockout": {"max_attempts": 5, "duration_seconds": 300},
                    "two_factor": {
                        "enabled": False,
                        "enforced_roles": ["admin", "power_user"],
                        "remember_devices_minutes": 7 * 24 * 60,
                    },
                },
                "rbac": {
                    "enabled": True,
                    "default_role": "user",
                    "fallback_role": "guest",
                    "enforce_subscriptions": True,
                },
                "subscriptions": {
                    "enabled": False,
                    "default_tier": "standard",
                    "guest_tier": "free",
                    "tiers": {
                        "free": {
                            "title": "Free",
                            "role": "guest",
                            "limits": {"requests_per_minute": 10, "concurrent_tasks": 1},
                        },
                        "standard": {
                            "title": "Standard",
                            "role": "user",
                            "limits": {"requests_per_minute": 30, "concurrent_tasks": 2},
                        },
                        "pro": {
                            "title": "Pro",
                            "role": "power_user",
                            "limits": {"requests_per_minute": 60, "concurrent_tasks": 4},
                        },
                        "enterprise": {
                            "title": "Enterprise",
                            "role": "admin",
                            "limits": {"requests_per_minute": 120, "concurrent_tasks": 10},
                        },
                    },
                    "user_assignments": {},
                    "user_id_assignments": {},
                },
                "execution": {
                    "allow_scripts": False,
                    "allow_system_shell": False,
                    "restricted_extensions": ["bat", "cmd", "ps1", "js", "vbs"],
                },
                "settings": {"pin": "", "lock_after_minutes": 15},
                "ollama": {
                    "bind_address": "127.0.0.1",
                    "allow_external": False,
                    "launch_mode": "background",
                    "auto_restart": True,
                },
            },
            "audit": {
                "enabled": True,
                "max_log_size": 10 * 1024 * 1024,
                "max_log_age_days": 90,
            },
        }

        merged_config = copy.deepcopy(default_config)

        if self.config_file.exists():
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    loaded_config = json.load(f)
                migrated = self._migrate_legacy_config(loaded_config, default_config)
                merged_config = self._deep_update(merged_config, migrated)
            except Exception as e:
                print(f"Error loading config: {e}")
        else:
            # Create config file with defaults
            self.save_config(default_config)

        return merged_config

    def save_config(self, config_data: Optional[Dict[str, Any]] = None):
        """Save configuration to file"""
        if config_data is None:
            config_data = self.config_data

        # Create config directory if it doesn't exist
        self.config_file.parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(config_data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving config: {e}")

    def get(self, key: str, default=None):
        """Get configuration value by key (supports nested keys with dots)"""
        keys = key.split(".")
        value = self.config_data

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def set(self, key: str, value: Any):
        """Set configuration value by key (supports nested keys with dots)"""
        keys = key.split(".")
        config = self.config_data

        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]

        config[keys[-1]] = value
        self.save_config()

    def _deep_update(self, base: Dict[str, Any], updates: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively merge dictionaries"""
        for key, value in updates.items():
            if isinstance(value, dict) and isinstance(base.get(key), dict):
                base[key] = self._deep_update(base[key], value)
            else:
                base[key] = value
        return base

    def _migrate_legacy_config(self, loaded_config: Dict[str, Any], default_config: Dict[str, Any]) -> Dict[str, Any]:
        """Apply migrations for legacy configuration formats"""
        if not isinstance(loaded_config, dict):
            return {}

        migrated = copy.deepcopy(loaded_config)
        default_security = default_config.get("security", {})
        migrated = self._migrate_legacy_security(migrated, default_security)

        # Move legacy audit flag from security section
        security_section = migrated.get("security")
        audit_enabled_legacy = None
        if isinstance(security_section, dict) and "audit_enabled" in security_section:
            audit_enabled_legacy = security_section.pop("audit_enabled")

        audit_defaults = default_config.get("audit", {})
        if "audit" not in migrated:
            migrated["audit"] = copy.deepcopy(audit_defaults)
        elif isinstance(migrated["audit"], dict) and isinstance(audit_defaults, dict):
            migrated["audit"] = self._deep_update(copy.deepcopy(audit_defaults), migrated["audit"])

        if audit_enabled_legacy is not None and isinstance(migrated.get("audit"), dict):
            migrated["audit"]["enabled"] = bool(audit_enabled_legacy)

        return migrated

    def _migrate_legacy_security(self, config_data: Dict[str, Any], default_security: Dict[str, Any]) -> Dict[str, Any]:
        """Upgrade legacy security section to the new nested structure"""
        security = config_data.get("security")

        if not isinstance(security, dict):
            config_data["security"] = copy.deepcopy(default_security)
            return config_data

        legacy_keys = {
            "auth_enabled",
            "2fa_enabled",
            "session_timeout_minutes",
            "allow_scripts",
            "settings_pin",
            "ollama_bind_address",
            "ollama_allow_external",
            "ollama_launch_mode",
            "require_login",
            "rbac_enabled",
            "default_role",
        }

        if any(key in security for key in legacy_keys):
            new_security = copy.deepcopy(default_security)

            new_security["auth"]["enabled"] = bool(security.get("auth_enabled", new_security["auth"]["enabled"]))
            new_security["auth"]["require_login"] = bool(
                security.get("require_login", new_security["auth"]["require_login"])
            )
            if "session_timeout_minutes" in security:
                new_security["auth"]["session_timeout_minutes"] = security.get("session_timeout_minutes")
            new_security["auth"]["two_factor"]["enabled"] = bool(
                security.get("2fa_enabled", new_security["auth"]["two_factor"]["enabled"])
            )

            if "allow_scripts" in security:
                new_security["execution"]["allow_scripts"] = bool(security.get("allow_scripts"))
            if "settings_pin" in security:
                new_security["settings"]["pin"] = security.get("settings_pin", "")
            if "ollama_bind_address" in security:
                new_security["ollama"]["bind_address"] = security["ollama_bind_address"]
            if "ollama_allow_external" in security:
                new_security["ollama"]["allow_external"] = bool(security["ollama_allow_external"])
            if "ollama_launch_mode" in security:
                new_security["ollama"]["launch_mode"] = str(security["ollama_launch_mode"]).lower()
            if "rbac_enabled" in security:
                new_security["rbac"]["enabled"] = bool(security["rbac_enabled"])
            if "default_role" in security:
                new_security["rbac"]["default_role"] = str(security["default_role"])

            config_data["security"] = new_security
        else:
            config_data["security"] = self._deep_update(copy.deepcopy(default_security), security)

        return config_data

    def get_ollama_models(self):
        """Get available LLM models"""
        return []

    def get_default_model(self):
        """Get default LLM model"""
        return self.get("llm.default_model", "auto")

    def get_ollama_url(self):
        """Get Ollama server URL"""
        return self.get("llm.ollama_url", "http://localhost:11434")

    def get_user_name(self):
        """Get user name"""
        return self.get("user.name", "Пользователь")

    def get_user_city(self):
        """Get user city"""
        return self.get("user.city", "Киев")

    # ---- Auth / Server getters ----
    def get_auth_server_url(self) -> str:
        return str(self.get("security.auth.server_url", "http://127.0.0.1:8000") or "http://127.0.0.1:8000")

    def is_remote_auth_enabled(self) -> bool:
        return bool(self.get("security.auth.use_remote_server", False))

    def is_remote_fallback_local(self) -> bool:
        return bool(self.get("security.auth.fallback_to_local", True))

    def is_auto_guest_on_failure(self) -> bool:
        return bool(self.get("security.auth.auto_login_guest_on_failure", False))

    def get_ollama_launch_mode(self) -> str:
        """Get configured launch mode for Ollama server."""
        try:
            launch_mode = self.get("security.ollama.launch_mode")
            if not launch_mode:
                launch_mode = self.get("startup.ollama_launch_mode")
            return str(launch_mode or "background").lower()
        except Exception:
            return "background"

    # ---- TTS Factory Methods (Days 4-5) ----
    def get_enabled_tts_engines(self) -> list:
        """Get list of enabled TTS engines.
        
        Returns:
            List of engine names that are enabled in config
        """
        engines = []
        try:
            engines_config = self.get("tts.engines", {})
            for engine_name, config in engines_config.items():
                if isinstance(config, dict) and config.get("enabled", True):
                    engines.append(engine_name)
        except Exception:
            pass
        
        # Fallback to legacy config
        if not engines:
            engines = ["silero"]
        
        return engines

    def get_tts_engine_config(self, engine_type: str) -> Dict[str, Any]:
        """Get configuration for specific TTS engine.
        
        Args:
            engine_type: Engine type (e.g., "silero", "bark")
            
        Returns:
            Engine configuration dictionary
        """
        try:
            return self.get(f"tts.engines.{engine_type}", {})
        except Exception:
            return {}

