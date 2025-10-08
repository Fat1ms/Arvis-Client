"""
Subprocess TTS worker to synthesize and play speech using Silero TTS
This isolates Silero's 'src' imports from the main app's packages.
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path
from typing import Any


def ensure_silero_paths():
    """Adjust sys.path to prefer Silero repo paths over project paths."""
    # Remove current working directory and project src from sys.path to avoid 'src' name clash
    cwd = os.path.abspath(os.getcwd())
    sys.path = [p for p in sys.path if os.path.abspath(p) not in (cwd, os.path.join(cwd, "src"))]

    # Try to locate torch hub cache of silero repo
    repo_root = Path.home() / ".cache" / "torch" / "hub" / "snakers4_silero-models_master"
    if repo_root.exists():
        repo_src = repo_root / "src"
        # Prepend repo paths
        sys.path.insert(0, str(repo_root))
        sys.path.insert(0, str(repo_src))


def map_voice(voice: str) -> str:
    # Provide a safe default mapping if a generic voice is passed
    if not voice:
        return "aidar"
    v = voice.lower().strip()
    if v in {"ru_v3", "ru-v3", "v3", "default"}:
        return "aidar"
    return voice


def _play_via_winsound_fallback(audio, sample_rate: int):
    """На Windows сохраняем WAV во временный файл и проигрываем через winsound."""
    try:
        import tempfile
        import winsound

        import numpy as np
        import soundfile as sf

        # Конвертируем в int16 для совместимости с winsound
        if hasattr(audio, "dtype") and str(audio.dtype) != "int16":
            # Нормализуем float32 -> int16
            data = (audio * 32767.0).astype("int16")
        else:
            data = audio

        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            tmp_path = tmp.name
        # Сохраняем WAV (PCM_16)
        sf.write(tmp_path, data, samplerate=sample_rate, subtype="PCM_16")
        winsound.PlaySound(tmp_path, winsound.SND_FILENAME)
        try:
            os.remove(tmp_path)
        except Exception:
            pass
        print("Audio playback completed (winsound fallback)")
        return True
    except Exception as we:
        print(f"[TTS-WORKER-ERROR] winsound fallback failed: {we}", file=sys.stderr)
        return False


def synth_and_play(text: str, voice: str, sample_rate: int, device: str, output: str | None, sapi_enabled: bool = True):
    import warnings

    import sounddevice as sd
    import soundfile as sf
    import torch

    # Подавляем предупреждения PyTorch для чистого вывода
    warnings.filterwarnings("ignore", category=UserWarning)
    warnings.filterwarnings("ignore", category=FutureWarning)

    # Make sure silero repo is importable
    ensure_silero_paths()

    try:
        # Устанавливаем переменные окружения для подавления лишнего вывода
        os.environ["TOKENIZERS_PARALLELISM"] = "false"

        # Load model via torch.hub (will use cache when available)
        # Перенаправляем stdout во время загрузки модели
        import contextlib
        import io

        f = io.StringIO()
        with contextlib.redirect_stdout(f), contextlib.redirect_stderr(f):
            loaded = torch.hub.load(
                repo_or_dir="snakers4/silero-models",
                model="silero_tts",
                language="ru",
                speaker="v3_1_ru",
                verbose=False,
            )
            # В некоторых версиях возможен кортеж (model, example_text, ...)
            model = loaded[0] if isinstance(loaded, (tuple, list)) else loaded

        # Безопасно выбираем устройство: если cuda недоступна, откатываемся на cpu
        target_device = device
        try:
            if (
                isinstance(target_device, str)
                and target_device.lower().startswith("cuda")
                and not torch.cuda.is_available()
            ):
                target_device = "cpu"
        except Exception:
            target_device = "cpu"

        model_any: Any = model
        model_any.to(target_device)
        voice = map_voice(voice)

        # Генерируем аудио с подавлением вывода
        with contextlib.redirect_stdout(f), contextlib.redirect_stderr(f):
            audio = model_any.apply_tts(text=text, speaker=voice, sample_rate=sample_rate)

        # Convert to numpy array
        if torch.is_tensor(audio):
            audio = audio.cpu().numpy()

        if output:
            sf.write(output, audio, sample_rate)
            print(f"Audio saved to: {output}")
        else:
            try:
                sd.play(audio, samplerate=sample_rate)
                sd.wait()
                print("Audio playback completed")
            except Exception as pe:
                # Частые причины на Windows: unsupported sample rate / WASAPI ошибки.
                # Пытаемся безопасно воспроизвести через winsound.
                if os.name == "nt":
                    ok = _play_via_winsound_fallback(audio, sample_rate)
                    if not ok:
                        raise pe
                else:
                    raise pe

    except Exception as e:
        # Очищаем CUDA кэш если возможно
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        # Если Silero недоступен (например, нет интернета для hub.load),
        # на Windows используем системный SAPI как запасной вариант.
        if os.name == "nt" and sapi_enabled:
            try:
                import win32com.client as wincl

                speak = wincl.Dispatch("SAPI.SpVoice")
                speak.Speak(text)
                print("Audio playback completed (SAPI fallback)")
                return
            except Exception as sapi_err:
                print(f"[TTS-WORKER-ERROR] SAPI fallback failed: {sapi_err}", file=sys.stderr)
        raise e


def main():
    parser = argparse.ArgumentParser(description="Arvis Silero TTS worker (subprocess)")
    parser.add_argument("--text", required=True, help="Text to speak")
    parser.add_argument("--voice", default="aidar")
    parser.add_argument("--sample-rate", type=int, default=48000)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--output", default=None, help="Optional path to save WAV instead of playing")
    parser.add_argument("--sapi-enabled", action="store_true", help="Allow SAPI fallback on Windows")

    args = parser.parse_args()

    try:
        synth_and_play(
            text=args.text,
            voice=args.voice,
            sample_rate=args.sample_rate,
            device=args.device,
            output=args.output,
            sapi_enabled=bool(args.sapi_enabled),
        )
    except Exception as e:
        print(f"[TTS-WORKER-ERROR] {e}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
