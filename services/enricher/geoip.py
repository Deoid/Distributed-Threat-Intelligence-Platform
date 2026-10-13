import hashlib
import ipaddress
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

# Fallback known threat actor IP mappings and realistic country pools
KNOWN_GEO_MAP = {
    "185.220.101.5": {"country": "Germany", "country_code": "DE", "city": "Frankfurt", "lat": 50.1109, "lon": 8.6821, "asn": "AS205120", "isp": "Tor Exit Node"},
    "45.155.205.233": {"country": "Russia", "country_code": "RU", "city": "Moscow", "lat": 55.7558, "lon": 37.6173, "asn": "AS48096", "isp": "Mir Telematiki LLC"},
    "193.142.146.88": {"country": "Netherlands", "country_code": "NL", "city": "Amsterdam", "lat": 52.3676, "lon": 4.9041, "asn": "AS200019", "isp": "Alexhost SRL"},
    "194.26.29.112": {"country": "Seychelles", "country_code": "SC", "city": "Victoria", "lat": -4.6191, "lon": 55.4513, "asn": "AS58061", "isp": "Scalaxy B.V."},
    "195.54.160.149": {"country": "Russia", "country_code": "RU", "city": "Saint Petersburg", "lat": 59.9343, "lon": 30.3351, "asn": "AS44050", "isp": "Petersburg Internet Network"},
    "185.190.140.8": {"country": "Bulgaria", "country_code": "BG", "city": "Sofia", "lat": 42.6977, "lon": 23.3219, "asn": "AS206804", "isp": "EstNOC OY"},
    "91.240.118.242": {"country": "Ukraine", "country_code": "UA", "city": "Kyiv", "lat": 50.4501, "lon": 30.5234, "asn": "AS200593", "isp": "Hostlife LLC"},
    "194.38.20.71": {"country": "United States", "country_code": "US", "city": "Secaucus", "lat": 40.7895, "lon": -74.0565, "asn": "AS202425", "isp": "IP Volume Inc"},
    "146.70.189.155": {"country": "United States", "country_code": "US", "city": "Los Angeles", "lat": 34.0522, "lon": -118.2437, "asn": "AS9009", "isp": "M247 Ltd"},
    "79.137.202.164": {"country": "France", "country_code": "FR", "city": "Paris", "lat": 48.8566, "lon": 2.3522, "asn": "AS16276", "isp": "OVH SAS"},
    "198.98.57.195": {"country": "United States", "country_code": "US", "city": "Piscataway", "lat": 40.5548, "lon": -74.4643, "asn": "AS29802", "isp": "ColoCrossing"},
    "103.251.167.20": {"country": "India", "country_code": "IN", "city": "Mumbai", "lat": 19.0760, "lon": 72.8777, "asn": "AS133982", "isp": "Spectranet India"},
    "42.236.10.125": {"country": "China", "country_code": "CN", "city": "Zhengzhou", "lat": 34.7466, "lon": 113.6253, "asn": "AS4134", "isp": "China Telecom"},
    "114.119.130.188": {"country": "Singapore", "country_code": "SG", "city": "Singapore", "lat": 1.3521, "lon": 103.8198, "asn": "AS45102", "isp": "Alibaba Cloud"},
    "218.92.0.188": {"country": "China", "country_code": "CN", "city": "Nanjing", "lat": 32.0603, "lon": 118.7969, "asn": "AS4134", "isp": "CHINANET Jiangsu"},
    "118.25.6.39": {"country": "China", "country_code": "CN", "city": "Shanghai", "lat": 31.2304, "lon": 121.4737, "asn": "AS45090", "isp": "Tencent Cloud"},
    "180.163.220.59": {"country": "China", "country_code": "CN", "city": "Beijing", "lat": 39.9042, "lon": 116.4074, "asn": "AS4808", "isp": "China Unicom"},
    "103.145.13.10": {"country": "Vietnam", "country_code": "VN", "city": "Hanoi", "lat": 21.0285, "lon": 105.8542, "asn": "AS135905", "isp": "Viettel Network"},
    "185.156.73.54": {"country": "United Kingdom", "country_code": "GB", "city": "London", "lat": 51.5074, "lon": -0.1278, "asn": "AS44477", "isp": "Stark Industries Solutions"},
    "89.248.165.73": {"country": "Netherlands", "country_code": "NL", "city": "Haarlem", "lat": 52.3874, "lon": 4.6462, "asn": "AS202425", "isp": "Recubed Global"},
    "195.22.126.155": {"country": "Italy", "country_code": "IT", "city": "Rome", "lat": 41.9028, "lon": 12.4964, "asn": "AS3269", "isp": "Telecom Italia"},
    "162.243.103.11": {"country": "United States", "country_code": "US", "city": "New York", "lat": 40.7128, "lon": -74.0060, "asn": "AS14061", "isp": "DigitalOcean LLC"},
    "104.244.72.115": {"country": "Luxembourg", "country_code": "LU", "city": "Roeser", "lat": 49.5372, "lon": 6.1461, "asn": "AS53667", "isp": "PONYNET"},
    "45.33.32.156": {"country": "United States", "country_code": "US", "city": "Dallas", "lat": 32.7767, "lon": -96.7970, "asn": "AS63949", "isp": "Linode LLC"}
}

COUNTRY_POOL = [
    {"country": "United States", "country_code": "US", "city": "Chicago", "lat": 41.8781, "lon": -87.6298, "asn": "AS15169", "isp": "Google Cloud"},
    {"country": "China", "country_code": "CN", "city": "Beijing", "lat": 39.9042, "lon": 116.4074, "asn": "AS4134", "isp": "China Telecom"},
    {"country": "Russia", "country_code": "RU", "city": "Saint Petersburg", "lat": 59.9343, "lon": 30.3351, "asn": "AS12389", "isp": "Rostelecom"},
    {"country": "Germany", "country_code": "DE", "city": "Frankfurt", "lat": 50.1109, "lon": 8.6821, "asn": "AS24940", "isp": "Hetzner Online"},
    {"country": "Netherlands", "country_code": "NL", "city": "Amsterdam", "lat": 52.3676, "lon": 4.9041, "asn": "AS1103", "isp": "SURFnet"},
    {"country": "Brazil", "country_code": "BR", "city": "Sao Paulo", "lat": -23.5505, "lon": -46.6333, "asn": "AS28573", "isp": "Claro Brasil"},
    {"country": "India", "country_code": "IN", "city": "Bengaluru", "lat": 12.9716, "lon": 77.5946, "asn": "AS55836", "isp": "Reliance Jio"},
    {"country": "United Kingdom", "country_code": "GB", "city": "London", "lat": 51.5074, "lon": -0.1278, "asn": "AS2856", "isp": "BT Group"},
    {"country": "France", "country_code": "FR", "city": "Paris", "lat": 48.8566, "lon": 2.3522, "asn": "AS16276", "isp": "OVH"},
    {"country": "Iran", "country_code": "IR", "city": "Tehran", "lat": 35.6892, "lon": 51.3890, "asn": "AS48159", "isp": "Telecommunication Company of Iran"},
    {"country": "South Korea", "country_code": "KR", "city": "Seoul", "lat": 37.5665, "lon": 126.9780, "asn": "AS9318", "isp": "SK Broadband"}
]

def resolve_geoip(ip: str) -> Dict[str, Any]:
    """
    Deterministically and reliably resolve IP geolocation metadata.
    Uses known threat actor table first, then hash-based distribution over country pool
    to ensure offline, fast, repeatable enrichment.
    """
    if ip in KNOWN_GEO_MAP:
        return KNOWN_GEO_MAP[ip]

    # Handle private or loopback IPs
    try:
        ip_obj = ipaddress.ip_address(ip)
        if ip_obj.is_private or ip_obj.is_loopback:
            return {
                "country": "Internal Network",
                "country_code": "LO",
                "city": "Localhost / Private LAN",
                "lat": 0.0,
                "lon": 0.0,
                "asn": "AS0",
                "isp": "Private Enterprise Subnet"
            }
    except ValueError:
        pass

    # Deterministic assignment using md5 hash of IP address
    hash_val = int(hashlib.md5(ip.encode("utf-8")).hexdigest(), 16)
    idx = hash_val % len(COUNTRY_POOL)
    base = COUNTRY_POOL[idx].copy()

    # Add slight deterministic jitter to coordinates for distinct map rendering
    jitter_lat = ((hash_val % 100) - 50) / 100.0
    jitter_lon = (((hash_val // 100) % 100) - 50) / 100.0
    base["lat"] = round(base["lat"] + jitter_lat, 4)
    base["lon"] = round(base["lon"] + jitter_lon, 4)
    return base
