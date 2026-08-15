from ai_planner import check_ai_connection


result = check_ai_connection()

print("Status:", result["status"])
print("Message:", result["message"])

if result.get("model"):
    print("Model:", result["model"])
