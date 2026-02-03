"""
Advanced Network Mapper Flask Application
==========================================
A professional-grade network device mapping tool with real-time tracking,
caching, authentication, and comprehensive security features.

Author: Enhanced Version
Version: 2.0
"""

import os
import logging
import hashlib
from datetime import datetime, timedelta
from functools import wraps
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

import requests
from flask import Flask, request, jsonify, render_template, abort
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_caching import Cache
from flask_cors import CORS
from werkzeug.middleware.proxy_fix import ProxyFix
from dotenv import load_dotenv
import redis
from redis.exceptions import RedisError

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

# Configuration
class Config:
    """Application configuration"""
    SECRET_KEY = os.environ.get('SECRET_KEY', os.urandom(32).hex())
    
    # API Credentials
    WIGLE_API_NAME = os.environ.get('WIGLE_API_NAME')
    WIGLE_API_TOKEN = os.environ.get('WIGLE_API_TOKEN')
    OPENCELLID_API_KEY = os.environ.get('OPENCELLID_API_KEY')
    SHODAN_API_KEY = os.environ.get('SHODAN_API_KEY')
    
    # Redis Configuration
    REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
    
    # Cache Configuration
    CACHE_TYPE = 'redis'
    CACHE_REDIS_URL = REDIS_URL
    CACHE_DEFAULT_TIMEOUT = 300  # 5 minutes
    
    # Rate Limiting
    RATELIMIT_STORAGE_URL = REDIS_URL
    RATELIMIT_DEFAULT = "100 per hour"
    
    # Security
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max request size
    JSON_SORT_KEYS = False
    
    # API Timeouts
    API_TIMEOUT = 10
    
    # Coordinate Validation
    MAX_SEARCH_RADIUS = 0.1  # Maximum search radius in degrees (~11km)
    
    @classmethod
    def validate(cls):
        """Validate critical configuration"""
        missing = []
        if not cls.WIGLE_API_NAME:
            missing.append('WIGLE_API_NAME')
        if not cls.WIGLE_API_TOKEN:
            missing.append('WIGLE_API_TOKEN')
        if not cls.OPENCELLID_API_KEY:
            missing.append('OPENCELLID_API_KEY')
            
        if missing:
            logger.warning(f"Missing API credentials: {', '.join(missing)}. Using fallback mode.")

app.config.from_object(Config)
Config.validate()

# Initialize extensions
cache = Cache(app)
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Rate Limiter
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri=Config.RATELIMIT_STORAGE_URL
)

# Device Type Classification
class DeviceType(Enum):
    """Enumeration of device types"""
    ROUTER = "router"
    CAR = "car"
    TV = "tv"
    HEADPHONE = "headphone"
    DASHCAM = "dashcam"
    CAMERA = "camera"
    IOT = "iot"
    CELL_TOWER = "cell_tower"
    BLUETOOTH = "bluetooth"
    UNKNOWN = "unknown"

@dataclass
class Device:
    """Data class for network devices"""
    lat: float
    lon: float
    device_type: str
    timestamp: str
    ssid: Optional[str] = None
    bssid: Optional[str] = None
    cell_id: Optional[str] = None
    ip: Optional[str] = None
    vendor: Optional[str] = None
    signal: Optional[int] = None
    accuracy: Optional[int] = None
    info: Optional[str] = None
    
    def to_dict(self):
        """Convert to dictionary, excluding None values"""
        return {k: v for k, v in asdict(self).items() if v is not None}

# Classification Patterns
DEVICE_PATTERNS = {
    DeviceType.CAR: [
        "CAR", "FORD", "TOYOTA", "BMW", "TESLA", "SYNC", "MAZDA", "HONDA",
        "UCONNECT", "HYUNDAI", "LEXUS", "NISSAN", "MERCEDES", "AUDI", "VW",
        "VOLKSWAGEN", "CHEVROLET", "KIA", "SUBARU", "JEEP", "DODGE", "RAM"
    ],
    DeviceType.TV: [
        "TV", "BRAVIA", "VIZIO", "SAMSUNG", "LG", "ROKU", "FIRE", "SMARTVIEW",
        "KDL-", "ANDROIDTV", "CHROMECAST", "APPLETV", "HISENSE", "TCL", "SONY"
    ],
    DeviceType.HEADPHONE: [
        "HEADPHONE", "EARBUD", "BOSE", "SONY", "BEATS", "AUDIO", "AIRPOD",
        "JBL", "SENNHEISER", "JABRA", "SOUNDCORE", "ANKER", "SKULLCANDY"
    ],
    DeviceType.DASHCAM: [
        "DASHCAM", "DASH CAM", "DVR", "70MAI", "VIOFO", "GARMIN DASH",
        "BLACKVUE", "NEXTBASE", "THINKWARE"
    ],
    DeviceType.CAMERA: [
        "CAM", "SURVEILLANCE", "SECURITY", "NEST", "RING", "ARLO", "HIKVISION",
        "DAHUA", "REOLINK", "WYZE", "EUFY", "BLINK", "UNIFI", "AXIS"
    ],
    DeviceType.IOT: [
        "WATCH", "FITBIT", "GARMIN", "WHOOP", "IOT", "SMART", "ALEXA",
        "GOOGLE HOME", "ECHO", "SENSOR", "THERMOSTAT", "NEST", "ECOBEE"
    ]
}

class DeviceClassifier:
    """Advanced device classification system"""
    
    @staticmethod
    def classify(name: str, original_type: str = "unknown") -> str:
        """
        Classify device based on name patterns
        
        Args:
            name: Device name or SSID
            original_type: Fallback type if no match found
            
        Returns:
            Classified device type as string
        """
        if not name:
            return original_type
            
        name_upper = name.upper()
        
        # Check each device type pattern
        for device_type, patterns in DEVICE_PATTERNS.items():
            if any(pattern in name_upper for pattern in patterns):
                return device_type.value
                
        return original_type
    
    @staticmethod
    def get_icon(device_type: str) -> str:
        """Get emoji icon for device type"""
        icons = {
            DeviceType.ROUTER.value: "📡",
            DeviceType.CAR.value: "🚗",
            DeviceType.TV.value: "📺",
            DeviceType.HEADPHONE.value: "🎧",
            DeviceType.DASHCAM.value: "📹",
            DeviceType.CAMERA.value: "📷",
            DeviceType.IOT.value: "💡",
            DeviceType.CELL_TOWER.value: "🗼",
            DeviceType.BLUETOOTH.value: "📶",
        }
        return icons.get(device_type, "❓")

class CoordinateValidator:
    """Coordinate validation utilities"""
    
    @staticmethod
    def validate(lat: float, lon: float) -> Tuple[bool, Optional[str]]:
        """
        Validate latitude and longitude
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        if lat is None or lon is None:
            return False, "Missing coordinates"
            
        if not isinstance(lat, (int, float)) or not isinstance(lon, (int, float)):
            return False, "Coordinates must be numeric"
            
        if not (-90 <= lat <= 90):
            return False, f"Invalid latitude: {lat}. Must be between -90 and 90"
            
        if not (-180 <= lon <= 180):
            return False, f"Invalid longitude: {lon}. Must be between -180 and 180"
            
        return True, None
    
    @staticmethod
    def calculate_bounds(lat: float, lon: float, radius: float = 0.01) -> Dict[str, float]:
        """
        Calculate bounding box for search area
        
        Args:
            lat: Center latitude
            lon: Center longitude
            radius: Search radius in degrees (default ~1.1km)
            
        Returns:
            Dictionary with lat/lon ranges
        """
        # Limit maximum radius
        radius = min(radius, Config.MAX_SEARCH_RADIUS)
        
        return {
            'latrange1': lat - radius,
            'latrange2': lat + radius,
            'longrange1': lon - radius,
            'longrange2': lon + radius
        }

class APIClient:
    """Base class for API clients with error handling and caching"""
    
    def __init__(self, base_url: str, timeout: int = Config.API_TIMEOUT):
        self.base_url = base_url
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'NetworkMapper/2.0'
        })
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> Optional[Dict]:
        """
        Make HTTP request with error handling
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint
            **kwargs: Additional arguments for requests
            
        Returns:
            Response JSON or None on error
        """
        url = f"{self.base_url}{endpoint}"
        kwargs.setdefault('timeout', self.timeout)
        kwargs.setdefault('verify', True)
        
        try:
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.Timeout:
            logger.error(f"Timeout accessing {url}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Error accessing {url}: {str(e)}")
        except ValueError as e:
            logger.error(f"Invalid JSON response from {url}: {str(e)}")
        
        return None

class WigleAPI(APIClient):
    """WiGLE API client"""
    
    def __init__(self):
        super().__init__('https://api.wigle.net/api/v2')
        if Config.WIGLE_API_NAME and Config.WIGLE_API_TOKEN:
            self.session.auth = (Config.WIGLE_API_NAME, Config.WIGLE_API_TOKEN)
    
    @cache.memoize(timeout=300)
    def search_networks(self, lat: float, lon: float, radius: float = 0.01) -> List[Device]:
        """Search for WiFi networks"""
        bounds = CoordinateValidator.calculate_bounds(lat, lon, radius)
        
        data = self._make_request('GET', '/network/search', params=bounds)
        
        if not data:
            return []
            
        devices = []
        for network in data.get('results', []):
            device_type = DeviceClassifier.classify(
                network.get('ssid'),
                DeviceType.ROUTER.value
            )
            
            devices.append(Device(
                lat=network.get('trilat'),
                lon=network.get('trilong'),
                ssid=network.get('ssid'),
                bssid=network.get('netid'),
                vendor=network.get('vendor'),
                signal=network.get('level'),
                timestamp=network.get('lastupdt'),
                device_type=device_type
            ))
            
        return devices
    
    @cache.memoize(timeout=300)
    def search_bluetooth(self, lat: float, lon: float, radius: float = 0.01) -> List[Device]:
        """Search for Bluetooth devices"""
        bounds = CoordinateValidator.calculate_bounds(lat, lon, radius)
        
        data = self._make_request('GET', '/bluetooth/search', params=bounds)
        
        if not data:
            return []
            
        devices = []
        for device in data.get('results', []):
            name = device.get('name') or device.get('netid')
            device_type = DeviceClassifier.classify(name, DeviceType.BLUETOOTH.value)
            
            devices.append(Device(
                lat=device.get('trilat'),
                lon=device.get('trilong'),
                ssid=name,
                bssid=device.get('netid'),
                vendor=device.get('type') or DeviceType.BLUETOOTH.value.replace('_', ' ').title(),
                signal=device.get('level'),
                timestamp=device.get('lastupdt'),
                device_type=device_type
            ))
            
        return devices
    
    def search_by_ssid(self, ssid: str) -> List[Device]:
        """Search networks by SSID"""
        data = self._make_request('GET', '/network/search', params={'ssid': ssid})
        
        if not data:
            return []
            
        devices = []
        for network in data.get('results', []):
            device_type = DeviceClassifier.classify(
                network.get('ssid'),
                DeviceType.ROUTER.value
            )
            
            devices.append(Device(
                lat=network.get('trilat'),
                lon=network.get('trilong'),
                ssid=network.get('ssid'),
                bssid=network.get('netid'),
                vendor=network.get('vendor'),
                signal=network.get('level'),
                timestamp=network.get('lastupdt'),
                device_type=device_type
            ))
            
        return devices
    
    def search_by_bssid(self, bssid: str) -> List[Device]:
        """Search networks by BSSID/MAC address"""
        data = self._make_request('GET', '/network/search', params={'netid': bssid})
        
        if not data:
            return []
            
        devices = []
        for network in data.get('results', []):
            device_type = DeviceClassifier.classify(
                network.get('ssid'),
                DeviceType.ROUTER.value
            )
            
            devices.append(Device(
                lat=network.get('trilat'),
                lon=network.get('trilong'),
                ssid=network.get('ssid'),
                bssid=network.get('netid'),
                vendor=network.get('vendor'),
                signal=network.get('level'),
                timestamp=network.get('lastupdt'),
                device_type=device_type
            ))
            
        return devices

class OpenCellIDAPI(APIClient):
    """OpenCellID API client"""
    
    def __init__(self):
        super().__init__('https://us1.unwiredlabs.com/v2')
    
    @cache.memoize(timeout=600)
    def search_towers(self, lat: float, lon: float) -> List[Device]:
        """Search for cell towers"""
        if not Config.OPENCELLID_API_KEY:
            return []
            
        data = self._make_request('POST', '/process.php', json={
            "token": Config.OPENCELLID_API_KEY,
            "lat": lat,
            "lon": lon,
            "address": 0
        })
        
        if not data or data.get('status') != 'ok':
            return []
            
        devices = []
        for cell in data.get('cells', []):
            devices.append(Device(
                lat=cell.get('lat'),
                lon=cell.get('lon'),
                cell_id=str(cell.get('cellid')),
                signal=cell.get('signal'),
                accuracy=cell.get('accuracy'),
                timestamp=cell.get('updated'),
                device_type=DeviceType.CELL_TOWER.value,
                vendor=f"{cell.get('radio', 'Unknown').upper()} Tower"
            ))
            
        return devices

class ShodanAPI(APIClient):
    """Shodan API client"""
    
    def __init__(self):
        super().__init__('https://api.shodan.io')
    
    @cache.memoize(timeout=600)
    def search_geo(self, lat: float, lon: float, radius: float = 1) -> List[Device]:
        """Search for IoT devices by geolocation"""
        if not Config.SHODAN_API_KEY:
            return []
            
        data = self._make_request('GET', '/shodan/host/search', params={
            'key': Config.SHODAN_API_KEY,
            'query': f'geo:{lat},{lon},{radius}',
            'limit': 10
        })
        
        if not data:
            return []
            
        devices = []
        for match in data.get('matches', []):
            info = match.get('data', '')
            device_type = DeviceClassifier.classify(info, DeviceType.IOT.value)
            
            location = match.get('location', {})
            if location.get('latitude') and location.get('longitude'):
                devices.append(Device(
                    lat=location['latitude'],
                    lon=location['longitude'],
                    ip=match.get('ip_str'),
                    info=info[:100],
                    device_type=device_type,
                    vendor=match.get('org', 'Unknown'),
                    timestamp=datetime.utcnow().isoformat() + 'Z'
                ))
            
        return devices

# Initialize API clients
wigle_api = WigleAPI()
opencellid_api = OpenCellIDAPI()
shodan_api = ShodanAPI()

# Decorators
def require_api_key(f):
    """Decorator to require API key for sensitive endpoints"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        expected_key = os.environ.get('APP_API_KEY')
        
        if expected_key and api_key != expected_key:
            abort(401, description="Invalid or missing API key")
            
        return f(*args, **kwargs)
    return decorated_function

def validate_coordinates_decorator(f):
    """Decorator to validate lat/lon parameters"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        lat = request.args.get('lat', type=float)
        lon = request.args.get('lon', type=float)
        
        is_valid, error_msg = CoordinateValidator.validate(lat, lon)
        if not is_valid:
            return jsonify({"error": error_msg, "status": "invalid_input"}), 400
            
        return f(*args, **kwargs)
    return decorated_function

# Routes
@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')

@app.route('/map')
def wifi_map():
    """WiFi map interface"""
    return render_template('wifi-search.html')

@app.route('/api/health')
@limiter.exempt
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat() + 'Z',
        "version": "2.0"
    })

@app.route('/api/nearby')
@limiter.limit("30 per minute")
@validate_coordinates_decorator
def nearby():
    """
    Get nearby devices
    
    Query Parameters:
        lat (float): Latitude
        lon (float): Longitude
        mode (str): 'wifi', 'bluetooth', or 'all' (default: 'wifi')
        radius (float): Search radius in degrees (default: 0.01)
    """
    lat = request.args.get('lat', type=float)
    lon = request.args.get('lon', type=float)
    mode = request.args.get('mode', 'wifi')
    radius = min(request.args.get('radius', 0.01, type=float), Config.MAX_SEARCH_RADIUS)
    
    logger.info(f"Nearby search: lat={lat}, lon={lon}, mode={mode}, radius={radius}")
    
    devices = []
    
    try:
        if mode == 'bluetooth':
            # Bluetooth only
            devices.extend(wigle_api.search_bluetooth(lat, lon, radius))
        elif mode == 'all':
            # All device types
            devices.extend(wigle_api.search_networks(lat, lon, radius))
            devices.extend(wigle_api.search_bluetooth(lat, lon, radius))
            devices.extend(opencellid_api.search_towers(lat, lon))
            devices.extend(shodan_api.search_geo(lat, lon))
        else:
            # WiFi + Cell towers (default)
            devices.extend(wigle_api.search_networks(lat, lon, radius))
            devices.extend(opencellid_api.search_towers(lat, lon))
    
    except Exception as e:
        logger.error(f"Error in nearby search: {str(e)}", exc_info=True)
        return jsonify({
            "error": "Internal server error",
            "status": "error"
        }), 500
    
    # Convert to dict and add icons
    result_devices = []
    for device in devices:
        device_dict = device.to_dict()
        device_dict['icon'] = DeviceClassifier.get_icon(device.device_type)
        result_devices.append(device_dict)
    
    return jsonify({
        "devices": result_devices,
        "count": len(result_devices),
        "timestamp": datetime.utcnow().isoformat() + 'Z',
        "status": "success"
    })

@app.route('/api/search')
@limiter.limit("20 per minute")
def search():
    """
    Advanced search endpoint
    
    Query Parameters:
        type (str): 'location', 'ssid', 'bssid', or 'network'
        query (str): Search query
        radius (float): Search radius for location searches (default: 0.01)
    """
    search_type = request.args.get('type')
    query = request.args.get('query')
    
    if not search_type or not query:
        return jsonify({
            "error": "Missing search parameters",
            "status": "invalid_input"
        }), 400
    
    logger.info(f"Search: type={search_type}, query={query}")
    
    devices = []
    
    try:
        if search_type == 'location':
            try:
                lat, lon = map(float, query.split(','))
                is_valid, error_msg = CoordinateValidator.validate(lat, lon)
                if not is_valid:
                    return jsonify({"error": error_msg, "status": "invalid_input"}), 400
                
                radius = min(request.args.get('radius', 0.01, type=float), Config.MAX_SEARCH_RADIUS)
                
                devices.extend(wigle_api.search_networks(lat, lon, radius))
                devices.extend(opencellid_api.search_towers(lat, lon))
                devices.extend(shodan_api.search_geo(lat, lon))
            except ValueError:
                return jsonify({
                    "error": "Invalid location format. Use: lat,lon",
                    "status": "invalid_input"
                }), 400
                
        elif search_type == 'ssid':
            devices.extend(wigle_api.search_by_ssid(query))
            
        elif search_type == 'bssid':
            # Validate MAC address format
            if not all(c in '0123456789ABCDEFabcdef:' for c in query):
                return jsonify({
                    "error": "Invalid BSSID format",
                    "status": "invalid_input"
                }), 400
            devices.extend(wigle_api.search_by_bssid(query))
            
        elif search_type == 'network':
            devices.extend(shodan_api.search_geo(0, 0))  # Global search
            
        else:
            return jsonify({
                "error": f"Invalid search type: {search_type}",
                "status": "invalid_input"
            }), 400
    
    except Exception as e:
        logger.error(f"Error in search: {str(e)}", exc_info=True)
        return jsonify({
            "error": "Internal server error",
            "status": "error"
        }), 500
    
    # Convert to dict and add icons
    result_devices = []
    for device in devices:
        device_dict = device.to_dict()
        device_dict['icon'] = DeviceClassifier.get_icon(device.device_type)
        result_devices.append(device_dict)
    
    return jsonify({
        "devices": result_devices,
        "count": len(result_devices),
        "timestamp": datetime.utcnow().isoformat() + 'Z',
        "status": "success"
    })

@app.route('/api/stats')
@limiter.limit("10 per minute")
@validate_coordinates_decorator
def get_stats():
    """Get statistics about devices in area"""
    lat = request.args.get('lat', type=float)
    lon = request.args.get('lon', type=float)
    radius = min(request.args.get('radius', 0.05, type=float), Config.MAX_SEARCH_RADIUS)
    
    try:
        # Gather all devices
        all_devices = []
        all_devices.extend(wigle_api.search_networks(lat, lon, radius))
        all_devices.extend(wigle_api.search_bluetooth(lat, lon, radius))
        all_devices.extend(opencellid_api.search_towers(lat, lon))
        
        # Calculate statistics
        device_types = {}
        vendors = {}
        signal_strengths = []
        
        for device in all_devices:
            # Count device types
            device_types[device.device_type] = device_types.get(device.device_type, 0) + 1
            
            # Count vendors
            if device.vendor:
                vendors[device.vendor] = vendors.get(device.vendor, 0) + 1
            
            # Collect signal strengths
            if device.signal:
                signal_strengths.append(device.signal)
        
        # Calculate average signal
        avg_signal = sum(signal_strengths) / len(signal_strengths) if signal_strengths else None
        
        return jsonify({
            "total_devices": len(all_devices),
            "device_types": device_types,
            "top_vendors": dict(sorted(vendors.items(), key=lambda x: x[1], reverse=True)[:10]),
            "average_signal": round(avg_signal, 2) if avg_signal else None,
            "search_area": {
                "center": {"lat": lat, "lon": lon},
                "radius_km": round(radius * 111, 2)  # Convert degrees to km
            },
            "timestamp": datetime.utcnow().isoformat() + 'Z',
            "status": "success"
        })
        
    except Exception as e:
        logger.error(f"Error calculating stats: {str(e)}", exc_info=True)
        return jsonify({
            "error": "Error calculating statistics",
            "status": "error"
        }), 500

@app.route('/api/geo/towers')
@limiter.limit("20 per minute")
@validate_coordinates_decorator
def get_towers():
    """Get cell towers in area"""
    lat = request.args.get('lat', type=float)
    lon = request.args.get('lon', type=float)
    
    try:
        devices = opencellid_api.search_towers(lat, lon)
        
        towers = []
        for device in devices:
            tower_data = device.to_dict()
            tower_data['icon'] = DeviceClassifier.get_icon(device.device_type)
            towers.append(tower_data)
        
        return jsonify({
            "towers": towers,
            "count": len(towers),
            "timestamp": datetime.utcnow().isoformat() + 'Z',
            "status": "success"
        })
        
    except Exception as e:
        logger.error(f"Error fetching towers: {str(e)}", exc_info=True)
        return jsonify({
            "error": "Error fetching cell towers",
            "status": "error"
        }), 500

# Error handlers
@app.errorhandler(400)
def bad_request(e):
    """Handle bad request errors"""
    return jsonify({
        "error": str(e.description) if e.description else "Bad request",
        "status": "error",
        "code": 400
    }), 400

@app.errorhandler(401)
def unauthorized(e):
    """Handle unauthorized errors"""
    return jsonify({
        "error": str(e.description) if e.description else "Unauthorized",
        "status": "error",
        "code": 401
    }), 401

@app.errorhandler(404)
def not_found(e):
    """Handle not found errors"""
    return jsonify({
        "error": "Resource not found",
        "status": "error",
        "code": 404
    }), 404

@app.errorhandler(429)
def ratelimit_handler(e):
    """Handle rate limit errors"""
    return jsonify({
        "error": "Rate limit exceeded",
        "status": "error",
        "code": 429,
        "retry_after": e.description
    }), 429

@app.errorhandler(500)
def internal_error(e):
    """Handle internal server errors"""
    logger.error(f"Internal server error: {str(e)}", exc_info=True)
    return jsonify({
        "error": "Internal server error",
        "status": "error",
        "code": 500
    }), 500

# CLI Commands
@app.cli.command()
def test_apis():
    """Test API connections"""
    print("Testing API connections...\n")
    
    test_lat, test_lon = 51.505, -0.09
    
    # Test WiGLE
    print("Testing WiGLE API...")
    try:
        devices = wigle_api.search_networks(test_lat, test_lon)
        print(f"✓ WiGLE API: Found {len(devices)} networks")
    except Exception as e:
        print(f"✗ WiGLE API: {str(e)}")
    
    # Test OpenCellID
    print("Testing OpenCellID API...")
    try:
        towers = opencellid_api.search_towers(test_lat, test_lon)
        print(f"✓ OpenCellID API: Found {len(towers)} towers")
    except Exception as e:
        print(f"✗ OpenCellID API: {str(e)}")
    
    # Test Shodan
    print("Testing Shodan API...")
    try:
        devices = shodan_api.search_geo(test_lat, test_lon)
        print(f"✓ Shodan API: Found {len(devices)} devices")
    except Exception as e:
        print(f"✗ Shodan API: {str(e)}")
    
    print("\nAPI testing complete!")

if __name__ == "__main__":
    # Development server
    debug_mode = os.environ.get('FLASK_ENV') == 'development'
    port = int(os.environ.get('PORT', 8080))
    
    if debug_mode:
        logger.warning("Running in DEBUG mode - DO NOT use in production!")
    
    app.run(
        host="0.0.0.0",
        port=port,
        debug=debug_mode
    )
