import re
from pathlib import Path


def migrate_env():
    env_path = Path(".env")
    if not env_path.exists():
        print("No .env file found to migrate.")
        return

    content = env_path.read_text(encoding="utf-8")

    # 1. Replace YONCA_ prefix with ALIM_
    # We look for lines starting with optional whitespace, then YONCA_
    new_content = re.sub(r"^(?P<indent>\s*)YONCA_", r"\g<indent>ALIM_", content, flags=re.MULTILINE)

    # 2. Also replace specific legacy strings if they exist in comments or values
    # (Be careful not to replace random strings, but YONCA_ is pretty specific)

    if content != new_content:
        # Backup first
        backup_path = env_path.with_suffix(".env.bak")
        env_path.rename(backup_path)
        print(f"Backed up .env to {backup_path}")

        env_path.write_text(new_content, encoding="utf-8")
        print("✅ Migrated .env from YONCA_ to ALIM_ prefixes.")
    else:
        print("No YONCA_ prefixes found in .env.")


if __name__ == "__main__":
    migrate_env()
