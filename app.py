import math

import folium
import streamlit as st

from streamlit_folium import st_folium

from places import (
    get_city_coordinates,
    get_places_near_city
)

from routing import (
    get_walking_route,
    format_distance,
    format_duration
)


# ==================================================
# הגדרות
# ==================================================

st.set_page_config(
    page_title="AI Travel Agent",
    page_icon="✈️",
    layout="centered"
)

st.title("✈️ AI Travel Agent")

st.caption(
    "Prototype v0.8 — "
    "Real Places + Real Walking Routes"
)


# ==================================================
# קטגוריות
# ==================================================

CATEGORY_MAP = {
    "museum": "היסטוריה",
    "gallery": "תרבות",
    "park": "טבע",
    "attraction": "אטרקציות"
}


def get_place_type(osm_category):

    if osm_category in [
        "museum",
        "gallery"
    ]:
        return "indoor"

    return "outdoor"


# ==================================================
# מרחק אווירי
# ==================================================

def calculate_distance(
    lat1,
    lon1,
    lat2,
    lon2
):

    radius = 6371

    lat1 = math.radians(lat1)
    lon1 = math.radians(lon1)

    lat2 = math.radians(lat2)
    lon2 = math.radians(lon2)

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1)
        * math.cos(lat2)
        * math.sin(dlon / 2) ** 2
    )

    c = 2 * math.atan2(
        math.sqrt(a),
        math.sqrt(1 - a)
    )

    return radius * c


# ==================================================
# ניקוי המקומות
# ==================================================

def prepare_places(
    raw_places,
    city_lat,
    city_lon
):

    places = []
    used_names = set()

    for place in raw_places:

        if (
            place["lat"] is None
            or place["lon"] is None
        ):
            continue

        if place["name"] in used_names:
            continue

        used_names.add(
            place["name"]
        )

        category = CATEGORY_MAP.get(
            place["category"],
            "אטרקציות"
        )

        distance = calculate_distance(
            city_lat,
            city_lon,
            place["lat"],
            place["lon"]
        )

        places.append({
            "name": place["name"],
            "category": category,
            "osm_category": place["category"],
            "type": get_place_type(
                place["category"]
            ),
            "lat": place["lat"],
            "lon": place["lon"],
            "distance": distance
        })

    places.sort(
        key=lambda x: x["distance"]
    )

    return places


# ==================================================
# שעות
# ==================================================

def get_time_slots(pace):

    if pace == "רגוע":

        return [
            "10:00",
            "14:00",
            "18:00"
        ]

    if pace == "מאוזן":

        return [
            "09:30",
            "12:00",
            "15:30",
            "19:00"
        ]

    return [
        "09:00",
        "11:00",
        "13:30",
        "16:00",
        "19:00"
    ]


# ==================================================
# מנוע התכנון הנוכחי
# ==================================================

def create_trip(
    real_places,
    number_of_days,
    interests,
    pace
):

    if interests:

        filtered_places = [
            place
            for place in real_places
            if place["category"]
            in interests
        ]

        if not filtered_places:
            filtered_places = (
                real_places.copy()
            )

    else:

        filtered_places = (
            real_places.copy()
        )

    remaining_places = (
        filtered_places.copy()
    )

    time_slots = (
        get_time_slots(pace)
    )

    trip = []

    activity_id = 1


    for day_number in range(
        1,
        number_of_days + 1
    ):

        if not remaining_places:
            break

        activities = []


        # הפעילות הראשונה
        current_place = (
            remaining_places.pop(0)
        )


        for slot_index, time in enumerate(
            time_slots
        ):

            # מהפעילות השנייה:
            # בוחרים את המקום הקרוב ביותר
            # בקו אווירי למקום הקודם.

            if slot_index > 0:

                if not remaining_places:
                    break

                current_place = min(
                    remaining_places,
                    key=lambda place:
                    calculate_distance(
                        current_place["lat"],
                        current_place["lon"],
                        place["lat"],
                        place["lon"]
                    )
                )

                remaining_places.remove(
                    current_place
                )


            activities.append({
                "id": activity_id,
                "start_time": time,
                "name": current_place["name"],
                "category": current_place[
                    "category"
                ],
                "type": current_place["type"],
                "distance": current_place[
                    "distance"
                ],
                "lat": current_place["lat"],
                "lon": current_place["lon"],
                "locked": False,
                "source": "OpenStreetMap"
            })

            activity_id += 1


        trip.append({
            "day": day_number,
            "activities": activities
        })


    return trip


# ==================================================
# Cache למסלולי הליכה
# ==================================================

@st.cache_data(
    show_spinner=False,
    ttl=3600
)
def load_walking_route(
    activity_coordinates
):

    activities = [
        {
            "lat": lat,
            "lon": lon
        }
        for lat, lon
        in activity_coordinates
    ]

    return get_walking_route(
        activities
    )


# ==================================================
# יצירת המפה
# ==================================================

def create_day_map(
    activities,
    walking_route
):

    if not activities:
        return None


    center_lat = sum(
        activity["lat"]
        for activity in activities
    ) / len(activities)

    center_lon = sum(
        activity["lon"]
        for activity in activities
    ) / len(activities)


    day_map = folium.Map(
        location=[
            center_lat,
            center_lon
        ],
        zoom_start=14,
        tiles="OpenStreetMap",
        control_scale=True
    )


    # ==================================================
    # המסלול האמיתי ברחובות
    # ==================================================

    if walking_route:

        route_points = (
            walking_route[
                "route_points"
            ]
        )

        folium.PolyLine(
            route_points,
            weight=5,
            opacity=0.85,
            tooltip="מסלול הליכה"
        ).add_to(day_map)


    # ==================================================
    # סימוני הפעילויות
    # ==================================================

    for index, activity in enumerate(
        activities,
        start=1
    ):

        number_icon = folium.DivIcon(
            html=f"""
            <div style="
                width:34px;
                height:34px;
                border-radius:50%;
                background:#2563eb;
                color:white;
                display:flex;
                align-items:center;
                justify-content:center;
                font-size:16px;
                font-weight:bold;
                border:3px solid white;
                box-shadow:
                    0px 1px 5px
                    rgba(0,0,0,0.45);
            ">
                {index}
            </div>
            """
        )


        popup = folium.Popup(
            f"""
            <b>
                {index}.
                {activity['name']}
            </b>
            <br>

            שעה:
            {activity['start_time']}
            <br>

            קטגוריה:
            {activity['category']}
            """,
            max_width=300
        )


        folium.Marker(
            location=[
                activity["lat"],
                activity["lon"]
            ],
            tooltip=(
                f"{index}. "
                f"{activity['name']}"
            ),
            popup=popup,
            icon=number_icon
        ).add_to(day_map)


    # ==================================================
    # התאמת המפה לכל המסלול
    # ==================================================

    if walking_route:

        day_map.fit_bounds(
            walking_route[
                "route_points"
            ],
            padding=(30, 30)
        )

    else:

        points = [
            [
                activity["lat"],
                activity["lon"]
            ]
            for activity
            in activities
        ]

        day_map.fit_bounds(
            points,
            padding=(30, 30)
        )


    return day_map


# ==================================================
# ממשק
# ==================================================

destination = st.text_input(
    "לאן אתם טסים?",
    placeholder="לדוגמה: Rome"
)


days = st.number_input(
    "לכמה ימים?",
    min_value=1,
    max_value=14,
    value=3
)


travelers = st.number_input(
    "כמה אנשים נוסעים?",
    min_value=1,
    max_value=20,
    value=2
)


budget = st.selectbox(
    "מה רמת התקציב?",
    [
        "נמוך",
        "בינוני",
        "גבוה"
    ]
)


pace = st.selectbox(
    "איזה קצב טיול אתם אוהבים?",
    [
        "רגוע",
        "מאוזן",
        "עמוס"
    ]
)


interests = st.multiselect(
    "מה מעניין אתכם?",
    [
        "היסטוריה",
        "תרבות",
        "טבע",
        "אטרקציות"
    ]
)


notes = st.text_area(
    "משהו נוסף שחשוב שנדע?"
)


# ==================================================
# בניית הטיול
# ==================================================

if st.button(
    "✨ בנה לי טיול",
    type="primary"
):

    if not destination:

        st.warning(
            "צריך לכתוב יעד קודם."
        )

    else:

        try:

            with st.spinner(
                "מחפש מקומות ובונה מסלול..."
            ):

                location = (
                    get_city_coordinates(
                        destination
                    )
                )


                if location is None:

                    st.error(
                        "לא הצלחתי למצוא "
                        "את היעד."
                    )

                else:

                    raw_places = (
                        get_places_near_city(
                            location["lat"],
                            location["lon"]
                        )
                    )


                    real_places = (
                        prepare_places(
                            raw_places,
                            location["lat"],
                            location["lon"]
                        )
                    )


                    if not real_places:

                        st.error(
                            "לא נמצאו "
                            "מספיק מקומות."
                        )

                    else:

                        trip = create_trip(
                            real_places,
                            days,
                            interests,
                            pace
                        )


                        st.session_state[
                            "location"
                        ] = location

                        st.session_state[
                            "real_places"
                        ] = real_places

                        st.session_state[
                            "trip"
                        ] = trip

                        st.session_state[
                            "trip_info"
                        ] = {
                            "destination":
                            destination,

                            "travelers":
                            travelers,

                            "budget":
                            budget,

                            "pace":
                            pace,

                            "interests":
                            interests,

                            "notes":
                            notes
                        }


        except Exception as error:

            st.error(
                f"שגיאה: {error}"
            )


# ==================================================
# הצגת הטיול
# ==================================================

if "trip" in st.session_state:

    st.divider()

    info = (
        st.session_state[
            "trip_info"
        ]
    )

    location = (
        st.session_state[
            "location"
        ]
    )


    st.header(
        f"הטיול שלכם ל-"
        f"{info['destination']} 🌍"
    )


    st.caption(
        f"זוהה כ: "
        f"{location['name']}"
    )


    st.write(
        f"👥 {info['travelers']} נוסעים | "
        f"💰 תקציב {info['budget']} | "
        f"🚶 קצב {info['pace']}"
    )


    st.info(
        "המקומות והמיקומים אמיתיים. "
        "גם מסלולי ההליכה וזמני ההליכה "
        "מחושבים עכשיו לפי רשת הרחובות. "
        "שעות פתיחה ומחירים עדיין לא מחוברים."
    )


    # ==================================================
    # ימים
    # ==================================================

    for day in (
        st.session_state[
            "trip"
        ]
    ):

        with st.expander(
            f"📅 יום {day['day']}",
            expanded=True
        ):

            activities = (
                day["activities"]
            )


            if not activities:
                continue


            # ==================================================
            # קבלת מסלול הליכה אמיתי
            # ==================================================

            coordinates = tuple(
                (
                    activity["lat"],
                    activity["lon"]
                )
                for activity
                in activities
            )


            walking_route = None


            if len(activities) >= 2:

                try:

                    with st.spinner(
                        "מחשב מסלול הליכה..."
                    ):

                        walking_route = (
                            load_walking_route(
                                coordinates
                            )
                        )

                except Exception as error:

                    st.warning(
                        "לא הצלחתי כרגע "
                        "לקבל מסלול הליכה."
                    )


            legs = []

            if walking_route:

                legs = walking_route[
                    "legs"
                ]


            # ==================================================
            # הצגת הפעילויות
            # ==================================================

            for index, activity in enumerate(
                activities,
                start=1
            ):

                col1, col2 = (
                    st.columns(
                        [4, 1]
                    )
                )


                with col1:

                    if (
                        activity["type"]
                        == "indoor"
                    ):
                        icon = "🏠"
                    else:
                        icon = "☀️"


                    if activity["locked"]:
                        lock_icon = "🔒"
                    else:
                        lock_icon = ""


                    st.write(
                        f"**{index}. "
                        f"{activity['start_time']}** "
                        f"— {activity['name']} "
                        f"{icon} "
                        f"{lock_icon}"
                    )


                    st.caption(
                        f"🏷️ "
                        f"{activity['category']} | "
                        f"מקור: "
                        f"{activity['source']}"
                    )


                    # ==========================================
                    # זמן הליכה מהפעילות הקודמת
                    # ==========================================

                    if (
                        index > 1
                        and
                        len(legs)
                        >= index - 1
                    ):

                        leg = legs[
                            index - 2
                        ]


                        st.write(
                            "🚶 מהפעילות הקודמת: "
                            f"**"
                            f"{format_duration(leg['duration_s'])}"
                            f"**"
                            " · "
                            f"{format_distance(leg['distance_m'])}"
                        )


                with col2:

                    button_text = (
                        "פתח"
                        if activity["locked"]
                        else "נעל"
                    )


                    if st.button(
                        button_text,
                        key=(
                            f"lock_"
                            f"{activity['id']}"
                        )
                    ):

                        activity[
                            "locked"
                        ] = (
                            not activity[
                                "locked"
                            ]
                        )

                        st.rerun()


            # ==================================================
            # סיכום היום
            # ==================================================

            if walking_route:

                st.divider()

                st.write(
                    "🚶 **סה״כ הליכה בין "
                    "הפעילויות:** "
                    f"{format_distance(walking_route['distance_m'])}"
                )

                st.write(
                    "⏱️ **זמן הליכה מצטבר:** "
                    f"{format_duration(walking_route['duration_s'])}"
                )


            # ==================================================
            # מפה
            # ==================================================

            st.write(
                "### 🗺️ מסלול היום"
            )


            day_map = create_day_map(
                activities,
                walking_route
            )


            if day_map:

                st_folium(
                    day_map,
                    width=700,
                    height=500,
                    returned_objects=[]
                )