import time
import requests


ROUTING_URL = (
    "https://routing.openstreetmap.de/"
    "routed-foot/route/v1/driving"
)

HEADERS = {
    "User-Agent": "TravelAgentPrototype/0.1"
}


def get_walking_route(activities):
    """
    מקבל רשימת פעילויות לפי הסדר.

    מחזיר:
    - מסלול הליכה אמיתי ברחובות
    - מרחק כולל
    - זמן כולל
    - מרחק וזמן בין כל שתי פעילויות
    """

    if len(activities) < 2:
        return None

    # OSRM רוצה:
    # longitude,latitude
    coordinates = ";".join(
        f"{activity['lon']},{activity['lat']}"
        for activity in activities
    )

    url = (
        f"{ROUTING_URL}/{coordinates}"
    )

    params = {
        "overview": "full",
        "geometries": "geojson",
        "steps": "false"
    }

    # השירות הציבורי מבקש שימוש מתון.
    time.sleep(1.1)

    response = requests.get(
        url,
        params=params,
        headers=HEADERS,
        timeout=40
    )

    response.raise_for_status()

    data = response.json()

    if data.get("code") != "Ok":
        return None

    if not data.get("routes"):
        return None

    route = data["routes"][0]

    # GeoJSON מחזיר:
    # [longitude, latitude]
    #
    # Folium צריך:
    # [latitude, longitude]

    route_points = [
        [coordinate[1], coordinate[0]]
        for coordinate
        in route["geometry"]["coordinates"]
    ]

    legs = []

    for leg in route.get("legs", []):

        legs.append({
            "distance_m": leg["distance"],
            "duration_s": leg["duration"]
        })

    return {
        "route_points": route_points,
        "distance_m": route["distance"],
        "duration_s": route["duration"],
        "legs": legs
    }


def format_distance(distance_m):
    """
    ממיר מטרים לתצוגה נוחה.
    """

    if distance_m < 1000:
        return f"{round(distance_m)} מטר"

    return f"{distance_m / 1000:.1f} ק״מ"


def format_duration(duration_s):
    """
    ממיר שניות לדקות/שעות.
    """

    minutes = round(duration_s / 60)

    if minutes < 60:
        return f"{minutes} דקות"

    hours = minutes // 60
    remaining_minutes = minutes % 60

    if remaining_minutes == 0:
        return f"{hours} שעות"

    return (
        f"{hours} שעות ו-"
        f"{remaining_minutes} דקות"
    )