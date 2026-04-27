import json
from pathlib import Path


def main() -> None:
    conversation_dir = Path("workspace/conversations")
    for file_path in sorted(conversation_dir.glob("*.jsonl")):
        print(f"# {file_path.name}")
        for line in file_path.read_text(encoding="utf-8").splitlines():
            record = json.loads(line)
            role = record["role"].upper()
            print(f"[{record['timestamp']}] {role}: {record['content']}")


if __name__ == "__main__":
    main()
