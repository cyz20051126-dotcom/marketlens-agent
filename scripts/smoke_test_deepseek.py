"""Quick smoke test: load .env, call DeepSeek, verify key works.

Run with:
    C:\\Users\\chenyizhe\\.workbuddy\\binaries\\python\\envs\\marketlens\\Scripts\\python.exe scripts/smoke_test_deepseek.py
"""
import os
import sys
from pathlib import Path

# Load .env manually (avoid python-dotenv dependency in this script)
env_path = Path(__file__).resolve().parent.parent / ".env"
if env_path.exists():
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip())

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from marketlens.agent.llm import DeepSeekLLMClient  # noqa: E402

client = DeepSeekLLMClient()
print(f"provider class: {type(client).__name__}")
print(f"api_key present: {bool(client.api_key)}")
print(f"api_key prefix: {client.api_key[:6]}...")
print(f"base_url: {client.base_url}")
print(f"model: {client.model}")
print()

print("calling deepseek with a simple prompt...")
result = client.complete(
    system_prompt="You are a helpful assistant. Reply in one short Chinese sentence.",
    user_prompt="\u7528\u4e00\u53e5\u8bdd\u8bf4\u660e\u745e\u5e78\u5496\u5561\u662f\u4ec0\u4e48\u3002",
)

print(f"result.provider: {result.provider}")
print(f"result.content:")
print(result.content)
print()

if result.provider == "deepseek":
    print("=== SMOKE TEST PASSED: DeepSeek key works ===")
    sys.exit(0)
else:
    print("=== SMOKE TEST FAILED: fell back to offline mode ===")
    print("check .env DEEPSEEK_API_KEY / DEEPSEEK_BASE_URL / network")
    sys.exit(1)
