import argparse
import datetime
import sys
from typing import Dict

# Try toml first (read+write). Fallback to tomllib for read and manual write.
try:
    import toml  # type: ignore
    HAS_TOML = True
except Exception:
    HAS_TOML = False

try:
    import tomllib  # Python 3.11+
    HAS_TOMLLIB = True
except Exception:
    HAS_TOMLLIB = False

if not HAS_TOML and not HAS_TOMLLIB:
    print("Error: Neither 'toml' nor 'tomllib' is available. Install 'toml' (pip install toml).", file=sys.stderr)
    sys.exit(1)


def load_toml(path: str) -> Dict:
    if HAS_TOML:
        return toml.load(path)
    else:
        with open(path, "rb") as f:
            return tomllib.load(f)


def dump_toml(data: Dict, path: str) -> None:
    if HAS_TOML:
        with open(path, "w", encoding="utf-8") as f:
            toml.dump(data, f)
        return
    # Minimal manual serializer for our schema
    lines = []
    alem = data.get("alem", {})
    lines.append("[alem]")
    lines.append(f"version = \"{alem.get('version', '0.0.0')}\"")
    lines.append(f"updated_at = \"{alem.get('updated_at', '')}\"")
    lines.append("")

    models = data.get("models", {})
    for comp in ("nl_to_sql", "reasoner", "vision"):
        m = models.get(comp, {})
        lines.append(f"[models.{comp}]")
        lines.append(f"id = \"{m.get('id', '')}\"")
        lines.append(f"fingerprint = \"{m.get('fingerprint', '')}\"")
        lines.append("")

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines).strip() + "\n")


def bump_version(current: str, bump_type: str) -> str:
    try:
        major, minor, patch = [int(x) for x in current.split('.')]
    except Exception:
        major, minor, patch = 0, 0, 0
    if bump_type == "major":
        return f"{major + 1}.0.0"
    if bump_type == "minor":
        return f"{major}.{minor + 1}.0"
    # patch or default
    return f"{major}.{minor}.{patch + 1}"


def main():
    parser = argparse.ArgumentParser(description="CI auto-bump ALEM version when model identifiers change.")
    parser.add_argument("--file", default="alem_version.toml", help="Path to the ALEM version TOML file.")
    parser.add_argument("--component", required=True, choices=["nl_to_sql", "reasoner", "vision"], help="Target component to update.")
    parser.add_argument("--model-id", required=True, help="New model identifier (e.g., qwen3-235b).")
    parser.add_argument("--fingerprint", required=True, help="Model fingerprint/hash/version from provider.")
    parser.add_argument("--bump", choices=["auto", "major", "minor", "patch"], default="auto", help="Bump strategy. 'auto' bumps minor when changes detected.")

    args = parser.parse_args()

    data = load_toml(args.file)
    data.setdefault("alem", {})
    data.setdefault("models", {})
    data["models"].setdefault(args.component, {"id": "", "fingerprint": ""})

    comp = data["models"][args.component]
    changed = (comp.get("id") != args.model_id) or (comp.get("fingerprint") != args.fingerprint)

    comp["id"] = args.model_id
    comp["fingerprint"] = args.fingerprint

    # Determine bump
    current_version = data["alem"].get("version", "0.0.0")
    bump_type = "minor" if (args.bump == "auto" and changed) else (args.bump if args.bump != "auto" else "patch")
    new_version = bump_version(current_version, bump_type)

    # Update timestamp
    data["alem"]["version"] = new_version
    data["alem"]["updated_at"] = datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"

    dump_toml(data, args.file)

    print(f"Updated {args.file}")
    print(f"Component: {args.component}")
    print(f"Version: {current_version} -> {new_version}")
    print(f"Model ID: {args.model_id}")
    print(f"Fingerprint: {args.fingerprint}")


if __name__ == "__main__":
    main()
