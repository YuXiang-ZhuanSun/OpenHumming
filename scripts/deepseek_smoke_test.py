import sys

from openai import OpenAI

from openhumming.config import get_settings


def main() -> int:
    settings = get_settings()
    if not settings.deepseek_api_key:
        print("OPENHUMMING_DEEPSEEK_API_KEY is not configured.")
        return 1

    prompt = sys.argv[1] if len(sys.argv) > 1 else "Reply with exactly: DEEPSEEK_OK"
    client = OpenAI(
        api_key=settings.deepseek_api_key,
        base_url=settings.deepseek_base_url,
    )
    response = client.chat.completions.create(
        model=settings.deepseek_model,
        messages=[
            {"role": "system", "content": "You are a concise test assistant."},
            {"role": "user", "content": prompt},
        ],
        stream=False,
    )
    content = (response.choices[0].message.content or "").strip()
    print(f"model={settings.deepseek_model}")
    print(f"reply={content}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
