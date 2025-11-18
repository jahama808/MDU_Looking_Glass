#!/usr/bin/env python3
"""
Hawaiian Island Detection Module

Determines which Hawaiian island a property/network is on based on:
1. City name
2. ZIP code
3. Geographic coordinates (lat/long)
"""

# City to Island mapping
CITY_TO_ISLAND = {
    # Oahu
    'HONOLULU': 'Oahu',
    'WAIKIKI': 'Oahu',
    'AIEA': 'Oahu',
    'EWA BEACH': 'Oahu',
    'KAPOLEI': 'Oahu',
    'PEARL CITY': 'Oahu',
    'WAIPAHU': 'Oahu',
    'MILILANI': 'Oahu',
    'MILILANI TOWN': 'Oahu',
    'WAHIAWA': 'Oahu',
    'KANEOHE': 'Oahu',
    'KAILUA': 'Oahu',
    'HALEIWA': 'Oahu',
    'WAIANAE': 'Oahu',
    'MAKAHA': 'Oahu',
    'HAWAII KAI': 'Oahu',
    'HAUULA': 'Oahu',
    'WAIMANALO': 'Oahu',
    'LAIE': 'Oahu',
    'KAHUKU': 'Oahu',

    # Maui
    'LAHAINA': 'Maui',
    'KAHULUI': 'Maui',
    'WAILUKU': 'Maui',
    'KIHEI': 'Maui',
    'WAILEA': 'Maui',
    'MAKAWAO': 'Maui',
    'PAIA': 'Maui',
    'HANA': 'Maui',
    'KAANAPALI': 'Maui',
    'KAPALUA': 'Maui',
    'MAALAEA': 'Maui',
    'PUKALANI': 'Maui',
    'KULA': 'Maui',
    'HAIKU': 'Maui',

    # Hawaii (Big Island)
    'HILO': 'Hawaii',
    'KONA': 'Hawaii',
    'KAILUA-KONA': 'Hawaii',
    'KAILUA KONA': 'Hawaii',
    'WAIKOLOA': 'Hawaii',
    'KAMUELA': 'Hawaii',
    'WAIMEA': 'Hawaii',
    'CAPTAIN COOK': 'Hawaii',
    'VOLCANO': 'Hawaii',
    'PAHOA': 'Hawaii',
    'NAALEHU': 'Hawaii',
    'HONOKAA': 'Hawaii',
    'KAPAAU': 'Hawaii',
    'HOLUALOA': 'Hawaii',
    'KEAUHOU': 'Hawaii',
    'KEALAKEKUA': 'Hawaii',
    'PAHALA': 'Hawaii',

    # Kauai
    'LIHUE': 'Kauai',
    'KAPAA': 'Kauai',
    'POIPU': 'Kauai',
    'PRINCEVILLE': 'Kauai',
    'HANALEI': 'Kauai',
    'KOLOA': 'Kauai',
    'KALAHEO': 'Kauai',
    'HANAPEPE': 'Kauai',
    'WAIMEA': 'Kauai',
    'KEKAHA': 'Kauai',
    'KILAUEA': 'Kauai',
    'ANAHOLA': 'Kauai',
    'ELEELE': 'Kauai',

    # Molokai
    'KAUNAKAKAI': 'Molokai',
    'HOOLEHUA': 'Molokai',
    'MAUNALOA': 'Molokai',

    # Lanai
    'LANAI CITY': 'Lanai',
}

# ZIP code to Island mapping
ZIP_TO_ISLAND = {
    # Oahu ZIP codes
    '96701': 'Oahu', '96706': 'Oahu', '96707': 'Oahu', '96709': 'Oahu',
    '96712': 'Oahu', '96717': 'Oahu', '96730': 'Oahu', '96731': 'Oahu',
    '96734': 'Oahu', '96744': 'Oahu', '96762': 'Oahu', '96782': 'Oahu',
    '96786': 'Oahu', '96789': 'Oahu', '96791': 'Oahu', '96792': 'Oahu',
    '96797': 'Oahu', '96801': 'Oahu', '96802': 'Oahu', '96803': 'Oahu',
    '96804': 'Oahu', '96805': 'Oahu', '96806': 'Oahu', '96807': 'Oahu',
    '96808': 'Oahu', '96809': 'Oahu', '96810': 'Oahu', '96811': 'Oahu',
    '96812': 'Oahu', '96813': 'Oahu', '96814': 'Oahu', '96815': 'Oahu',
    '96816': 'Oahu', '96817': 'Oahu', '96818': 'Oahu', '96819': 'Oahu',
    '96820': 'Oahu', '96821': 'Oahu', '96822': 'Oahu', '96823': 'Oahu',
    '96824': 'Oahu', '96825': 'Oahu', '96826': 'Oahu', '96828': 'Oahu',
    '96830': 'Oahu', '96836': 'Oahu', '96837': 'Oahu', '96838': 'Oahu',
    '96839': 'Oahu', '96840': 'Oahu', '96841': 'Oahu', '96843': 'Oahu',
    '96844': 'Oahu', '96846': 'Oahu', '96847': 'Oahu', '96848': 'Oahu',
    '96849': 'Oahu', '96850': 'Oahu', '96853': 'Oahu', '96854': 'Oahu',
    '96857': 'Oahu', '96858': 'Oahu', '96859': 'Oahu', '96860': 'Oahu',
    '96861': 'Oahu', '96863': 'Oahu', '96898': 'Oahu',

    # Maui ZIP codes
    '96708': 'Maui', '96713': 'Maui', '96732': 'Maui', '96753': 'Maui',
    '96761': 'Maui', '96768': 'Maui', '96779': 'Maui', '96790': 'Maui',
    '96793': 'Maui',

    # Hawaii (Big Island) ZIP codes
    '96704': 'Hawaii', '96710': 'Hawaii', '96719': 'Hawaii', '96720': 'Hawaii',
    '96721': 'Hawaii', '96725': 'Hawaii', '96726': 'Hawaii', '96727': 'Hawaii',
    '96728': 'Hawaii', '96737': 'Hawaii', '96738': 'Hawaii', '96740': 'Hawaii',
    '96743': 'Hawaii', '96749': 'Hawaii', '96750': 'Hawaii', '96755': 'Hawaii',
    '96760': 'Hawaii', '96764': 'Hawaii', '96771': 'Hawaii', '96776': 'Hawaii',
    '96777': 'Hawaii', '96778': 'Hawaii', '96780': 'Hawaii', '96781': 'Hawaii',
    '96783': 'Hawaii', '96785': 'Hawaii',

    # Kauai ZIP codes
    '96703': 'Kauai', '96705': 'Kauai', '96714': 'Kauai', '96716': 'Kauai',
    '96722': 'Kauai', '96741': 'Kauai', '96742': 'Kauai', '96746': 'Kauai',
    '96751': 'Kauai', '96752': 'Kauai', '96754': 'Kauai', '96756': 'Kauai',
    '96765': 'Kauai', '96766': 'Kauai', '96769': 'Kauai', '96796': 'Kauai',

    # Molokai ZIP codes
    '96729': 'Molokai', '96748': 'Molokai', '96757': 'Molokai', '96770': 'Molokai',

    # Lanai ZIP codes
    '96763': 'Lanai',
}

# Island bounding boxes (approximate)
# Format: (min_lat, max_lat, min_lon, max_lon)
ISLAND_BOUNDARIES = {
    'Oahu': (21.25, 21.72, -158.28, -157.65),
    'Maui': (20.57, 21.03, -156.69, -155.96),
    'Hawaii': (18.91, 20.27, -156.07, -154.81),
    'Kauai': (21.87, 22.23, -159.79, -159.29),
    'Molokai': (21.08, 21.21, -157.33, -156.75),
    'Lanai': (20.72, 20.91, -157.08, -156.78),
}


def detect_island_from_city(city):
    """
    Detect island from city name.

    Args:
        city: City name (string)

    Returns:
        Island name or None if not found
    """
    if not city:
        return None

    city_upper = city.upper().strip()
    return CITY_TO_ISLAND.get(city_upper)


def detect_island_from_zip(postal_code):
    """
    Detect island from ZIP/postal code.

    Args:
        postal_code: ZIP code (string or int)

    Returns:
        Island name or None if not found
    """
    if not postal_code:
        return None

    # Convert to string and extract first 5 digits
    zip_str = str(postal_code).strip()

    # Handle bytes
    if isinstance(postal_code, bytes):
        try:
            zip_str = postal_code.decode('utf-8')
        except:
            return None

    # Extract 5-digit ZIP
    zip_5 = zip_str[:5] if len(zip_str) >= 5 else zip_str

    return ZIP_TO_ISLAND.get(zip_5)


def detect_island_from_coordinates(latitude, longitude):
    """
    Detect island from geographic coordinates.

    Args:
        latitude: Latitude (float)
        longitude: Longitude (float)

    Returns:
        Island name or None if not found
    """
    if latitude is None or longitude is None:
        return None

    try:
        lat = float(latitude)
        lon = float(longitude)
    except (ValueError, TypeError):
        return None

    # Check each island's bounding box
    for island, (min_lat, max_lat, min_lon, max_lon) in ISLAND_BOUNDARIES.items():
        if min_lat <= lat <= max_lat and min_lon <= lon <= max_lon:
            return island

    return None


def detect_island(city=None, postal_code=None, latitude=None, longitude=None):
    """
    Detect Hawaiian island using multiple methods (city, ZIP, coordinates).

    Tries in order:
    1. City name
    2. ZIP code
    3. Coordinates

    Args:
        city: City name (optional)
        postal_code: ZIP code (optional)
        latitude: Latitude (optional)
        longitude: Longitude (optional)

    Returns:
        Island name or None if detection failed
    """
    # Try city first (most reliable for Hawaiian addresses)
    island = detect_island_from_city(city)
    if island:
        return island

    # Try ZIP code
    island = detect_island_from_zip(postal_code)
    if island:
        return island

    # Try coordinates
    island = detect_island_from_coordinates(latitude, longitude)
    if island:
        return island

    return None


if __name__ == '__main__':
    # Test cases
    test_cases = [
        {'city': 'Honolulu', 'expected': 'Oahu'},
        {'city': 'Lahaina', 'expected': 'Maui'},
        {'city': 'Hilo', 'expected': 'Hawaii'},
        {'city': 'Lihue', 'expected': 'Kauai'},
        {'postal_code': '96815', 'expected': 'Oahu'},
        {'postal_code': '96732', 'expected': 'Maui'},
        {'latitude': 21.3099, 'longitude': -157.8581, 'expected': 'Oahu'},  # Honolulu
        {'latitude': 20.8783, 'longitude': -156.6825, 'expected': 'Maui'},  # Lahaina
    ]

    print("Testing Island Detection")
    print("=" * 60)

    for i, test in enumerate(test_cases, 1):
        result = detect_island(**{k: v for k, v in test.items() if k != 'expected'})
        expected = test['expected']
        status = '✓' if result == expected else '✗'
        print(f"{status} Test {i}: {result} (expected: {expected})")
        if result != expected:
            print(f"   Input: {test}")
