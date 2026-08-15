from ai_planner import (
    build_trip_context,
    plan_trip_with_ai
)


sample_places = [
    {
        "name": "Colosseum",
        "category": "היסטוריה",
        "type": "outdoor",
        "lat": 41.8902,
        "lon": 12.4922,
        "distance": 1.2
    },
    {
        "name": "Pantheon",
        "category": "היסטוריה",
        "type": "indoor",
        "lat": 41.8986,
        "lon": 12.4769,
        "distance": 0.8
    }
]


sample_weather = [
    {
        "date": "2026-08-16",
        "description": "בעיקר בהיר",
        "max_temp": 32,
        "min_temp": 23,
        "rain_probability": 10
    }
]


context = build_trip_context(
    destination="Rome",
    number_of_days=3,
    travelers=2,
    budget="בינוני",
    pace="רגוע",
    interests=["היסטוריה"],
    notes="לא רוצים ללכת הרבה",
    places=sample_places,
    weather=sample_weather
)


print("=== TRIP CONTEXT ===")
print(context)

print()
print("=== AI PLAN TEST ===")

result = plan_trip_with_ai(context)

print("Status:", result["status"])
print("Message:", result["message"])
print("Model:", result.get("model"))

if result.get("plan"):
    print()
    print("=== PLAN ===")
    print(result["plan"])
