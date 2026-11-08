import sys
import os

# Set utf-8 stdout
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from tools.public_apis_tool import (
    search_public_apis,
    list_public_api_categories,
    get_random_public_api,
    refresh_public_apis_cache,
    get_all_public_apis
)
from agent_service import AntigravityAgent

print("=== 1. TEST DIRECT TOOL FUNCTIONS ===")
apis = get_all_public_apis()
print(f"Total APIs loaded: {len(apis)}")
assert len(apis) > 1000, "Should have more than 1000 public APIs"

search_res = search_public_apis(query="anime", limit=2)
print("Search anime preview:\n", search_res[:200], "...\n")
assert "DIREKTORI PUBLIC APIs" in search_res

cat_res = list_public_api_categories()
print("Category list preview:\n", cat_res[:200], "...\n")
assert "KATEGORI PUBLIC APIs" in cat_res

rand_res = get_random_public_api()
print("Random API preview:\n", rand_res[:200], "...\n")
assert "REKOMENDASI PUBLIC API ACAK" in rand_res

print("=== 2. TEST AGENT SERVICE INTEGRATION ===")
agent = AntigravityAgent()

# Check that tools are in llm_tools
tool_names = [t.__name__ for t in agent.llm_tools]
print(f"Total agent llm_tools: {len(tool_names)}")
assert "cari_public_api" in tool_names
assert "daftar_kategori_api" in tool_names
assert "rekomendasi_api_acak" in tool_names
assert "perbarui_database_api" in tool_names
print("✅ LLM tools registered successfully!")

# Ensure test sender is verified
test_sender = "test_user_public_api"
agent.security.verified_users.add(test_sender)

# Test agent intent shortcut: kategori api
resp1 = agent.process_message(test_sender, "kategori api")
print("Response for 'kategori api':\n", resp1[:200], "...\n")
assert "KATEGORI PUBLIC APIs" in resp1

# Test agent intent shortcut: cari api crypto
resp2 = agent.process_message(test_sender, "cari api crypto")
print("Response for 'cari api crypto':\n", resp2[:200], "...\n")
assert "DIREKTORI PUBLIC APIs" in resp2

# Test agent intent shortcut: api acak
resp3 = agent.process_message(test_sender, "api acak")
print("Response for 'api acak':\n", resp3[:200], "...\n")
assert "REKOMENDASI PUBLIC API ACAK" in resp3

# Test agent menu contains the new section
resp_menu = agent._get_help_menu("Sobat")
assert "Direktori Public APIs" in resp_menu
print("✅ Menu contains Public APIs section!")

print("\n🎉 ALL TESTS PASSED SUCCESSFULLY!")
