"""
Финальная проверка системы после исправления
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))


def run_all_checks():
    """Запустить все проверки"""
    print("=" * 70)
    print("ФИНАЛЬНАЯ ПРОВЕРКА СИСТЕМЫ")
    print("=" * 70)
    print()

    # 1. Проверка БД
    print("1️⃣  ПРОВЕРКА БАЗЫ ДАННЫХ")
    print("-" * 70)
    import sqlite3

    try:
        conn = sqlite3.connect("data/users.db")
        cursor = conn.cursor()

        # Проверка колонок
        cursor.execute("PRAGMA table_info(users)")
        columns = [col[1] for col in cursor.fetchall()]

        required_columns = ["backup_codes", "two_factor_setup_at"]
        missing = [col for col in required_columns if col not in columns]

        if missing:
            print(f"   ❌ Отсутствуют колонки: {missing}")
        else:
            print(f"   ✅ Все необходимые колонки присутствуют ({len(columns)} колонок)")

        # Проверка пользователей
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        print(f"   ✅ Пользователей в системе: {user_count}")

        # Проверка админа
        cursor.execute("SELECT username, role, is_active FROM users WHERE username='admin'")
        admin = cursor.fetchone()

        if admin:
            print(f"   ✅ Администратор найден: {admin[0]} ({admin[1]}, {'активен' if admin[2] else 'неактивен'})")
        else:
            print(f"   ❌ Администратор НЕ найден!")

        conn.close()

    except Exception as e:
        print(f"   ❌ Ошибка проверки БД: {e}")

    print()

    # 2. Проверка файла с паролем
    print("2️⃣  ПРОВЕРКА ФАЙЛА С ПАРОЛЕМ")
    print("-" * 70)
    password_file = Path("data/.admin_password.txt")
    if password_file.exists():
        with open(password_file, "r") as f:
            content = f.read()
            password_line = [line for line in content.split("\n") if "Password:" in line][0]
            password = password_line.split(": ")[1]
            print(f"   ✅ Файл существует")
            print(f"   📝 Пароль: {password}")
    else:
        print(f"   ⚠️  Файл отсутствует (это нормально, если уже удалён)")

    print()

    # 3. Тест входа
    print("3️⃣  ТЕСТ ВХОДА АДМИНИСТРАТОРА")
    print("-" * 70)
    try:
        from utils.security.auth import get_auth_manager

        auth_manager = get_auth_manager()
        session = auth_manager.authenticate("admin", "u1Y054gAxX1-pc6T")

        if session:
            user = auth_manager.validate_session(session.session_id)
            print(f"   ✅ Вход УСПЕШЕН!")
            print(f"   📋 Username: {user.username}")
            print(f"   🔑 Role: {user.role.value}")
            print(f"   🆔 Session: {session.session_id[:20]}...")
        else:
            print(f"   ❌ Вход НЕ УДАЛСЯ!")

    except Exception as e:
        print(f"   ❌ Ошибка входа: {e}")

    print()

    # 4. Проверка скриптов
    print("4️⃣  ПРОВЕРКА УТИЛИТ")
    print("-" * 70)
    scripts = ["migrate_db.py", "create_admin.py", "check_admin.py", "test_login.py"]

    for script in scripts:
        if Path(script).exists():
            print(f"   ✅ {script}")
        else:
            print(f"   ❌ {script} отсутствует")

    print()

    # 5. Проверка документации
    print("5️⃣  ПРОВЕРКА ДОКУМЕНТАЦИИ")
    print("-" * 70)
    docs = [
        "ADMIN_QUICKFIX.md",
        "ADMIN_LOGIN_CHEATSHEET.txt",
        "docs/ADMIN_LOGIN_FIX.md",
        "docs/ADMIN_LOGIN_FIX_REPORT.md",
    ]

    for doc in docs:
        if Path(doc).exists():
            print(f"   ✅ {doc}")
        else:
            print(f"   ❌ {doc} отсутствует")

    print()
    print("=" * 70)
    print("✅ ПРОВЕРКА ЗАВЕРШЕНА")
    print("=" * 70)
    print()
    print("📋 СЛЕДУЮЩИЕ ШАГИ:")
    print("   1. Запустите Arvis: python main.py")
    print("   2. Войдите как admin с паролем: u1Y054gAxX1-pc6T")
    print("   3. Смените пароль: ⚙️ → Безопасность → Смена пароля")
    print("   4. Удалите файл: Remove-Item data\\.admin_password.txt")
    print()


if __name__ == "__main__":
    run_all_checks()
