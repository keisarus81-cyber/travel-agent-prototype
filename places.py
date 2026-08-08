import requests


# ==================================================
# כתובת לחיפוש עיר
# ==================================================

NOMINATIM_URL = (
    "https://nominatim.openstreetmap.org/search"
)


# ==================================================
# כמה שרתי Overpass חלופיים
# ==================================================

OVERPASS_SERVERS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.private.coffee/api/interpreter",
    "https://maps.mail.ru/osm/tools/overpass/api/interpreter"
]


HEADERS = {
    "User-Agent": "TravelAgentPrototype/0.1"
}


# ==================================================
# מציאת עיר
# ==================================================

def get_city_coordinates(city_name):

    params = {
        "q": city_name,
        "format": "json",
        "limit": 1
    }

    response = requests.get(
        NOMINATIM_URL,
        params=params,
        headers=HEADERS,
        timeout=20
    )

    response.raise_for_status()

    results = response.json()

    if not results:
        return None

    return {
        "name": results[0]["display_name"],
        "lat": float(results[0]["lat"]),
        "lon": float(results[0]["lon"])
    }


# ==================================================
# שליחת בקשה ל-Overpass עם Fallback
# ==================================================

def send_overpass_request(query):

    last_error = None

    for server in OVERPASS_SERVERS:

        try:

            print(
                f"Trying Overpass server: {server}"
            )

            response = requests.post(
                server,
                data={
                    "data": query
                },
                headers=HEADERS,
                timeout=35
            )

            response.raise_for_status()

            return response.json()

        except (
            requests.RequestException,
            ValueError
        ) as error:

            print(
                f"Server failed: {server}"
            )

            print(
                f"Reason: {error}"
            )

            last_error = error

    raise RuntimeError(
        "All Overpass servers failed. "
        f"Last error: {last_error}"
    )


# ==================================================
# מציאת מקומות באזור העיר
# ==================================================

def get_places_near_city(lat, lon):

    query = f"""
    [out:json][timeout:20];

    (
        nwr(around:5000,{lat},{lon})
        ["tourism"="museum"];

        nwr(around:5000,{lat},{lon})
        ["tourism"="attraction"];

        nwr(around:5000,{lat},{lon})
        ["tourism"="gallery"];

        nwr(around:5000,{lat},{lon})
        ["leisure"="park"];
    );

    out center 40;
    """

    data = send_overpass_request(query)

    places = []


    # ==================================================
    # מעבר על המקומות שהתקבלו
    # ==================================================

    for element in data.get(
        "elements",
        []
    ):

        tags = element.get(
            "tags",
            {}
        )

        name = tags.get(
            "name"
        )


        # מקום ללא שם לא שימושי לנו
        if not name:
            continue


        # Nodes מכילים lat/lon ישירות.
        # Ways ו-Relations מקבלים center.
        latitude = element.get(
            "lat",
            element.get(
                "center",
                {}
            ).get("lat")
        )

        longitude = element.get(
            "lon",
            element.get(
                "center",
                {}
            ).get("lon")
        )


        if (
            latitude is None
            or longitude is None
        ):
            continue


        category = (
            tags.get("tourism")
            or tags.get("leisure")
            or "unknown"
        )


        places.append({
            "name": name,
            "category": category,
            "lat": latitude,
            "lon": longitude
        })


    return places