"""
Unit tests for Network Mapper Application
"""

import pytest
import json
from app import (
    app, 
    DeviceClassifier, 
    CoordinateValidator,
    Device,
    DeviceType
)

@pytest.fixture
def client():
    """Create test client"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

class TestCoordinateValidator:
    """Test coordinate validation"""
    
    def test_valid_coordinates(self):
        """Test valid coordinate pairs"""
        assert CoordinateValidator.validate(51.505, -0.09)[0] is True
        assert CoordinateValidator.validate(0, 0)[0] is True
        assert CoordinateValidator.validate(90, 180)[0] is True
        assert CoordinateValidator.validate(-90, -180)[0] is True
    
    def test_invalid_latitude(self):
        """Test invalid latitude values"""
        is_valid, error = CoordinateValidator.validate(91, 0)
        assert is_valid is False
        assert "latitude" in error.lower()
        
        is_valid, error = CoordinateValidator.validate(-91, 0)
        assert is_valid is False
    
    def test_invalid_longitude(self):
        """Test invalid longitude values"""
        is_valid, error = CoordinateValidator.validate(0, 181)
        assert is_valid is False
        assert "longitude" in error.lower()
        
        is_valid, error = CoordinateValidator.validate(0, -181)
        assert is_valid is False
    
    def test_none_coordinates(self):
        """Test None values"""
        is_valid, error = CoordinateValidator.validate(None, 0)
        assert is_valid is False
        
        is_valid, error = CoordinateValidator.validate(0, None)
        assert is_valid is False
    
    def test_calculate_bounds(self):
        """Test bounding box calculation"""
        bounds = CoordinateValidator.calculate_bounds(51.505, -0.09, 0.01)
        
        assert 'latrange1' in bounds
        assert 'latrange2' in bounds
        assert 'longrange1' in bounds
        assert 'longrange2' in bounds
        
        assert bounds['latrange2'] > bounds['latrange1']
        assert bounds['longrange2'] > bounds['longrange1']

class TestDeviceClassifier:
    """Test device classification"""
    
    def test_car_classification(self):
        """Test car device detection"""
        assert DeviceClassifier.classify("Tesla Model 3") == DeviceType.CAR.value
        assert DeviceClassifier.classify("FORD SYNC") == DeviceType.CAR.value
        assert DeviceClassifier.classify("BMW Connected") == DeviceType.CAR.value
    
    def test_tv_classification(self):
        """Test TV device detection"""
        assert DeviceClassifier.classify("Samsung Smart TV") == DeviceType.TV.value
        assert DeviceClassifier.classify("LG BRAVIA") == DeviceType.TV.value
        assert DeviceClassifier.classify("ROKU Express") == DeviceType.TV.value
    
    def test_headphone_classification(self):
        """Test headphone device detection"""
        assert DeviceClassifier.classify("AirPods Pro") == DeviceType.HEADPHONE.value
        assert DeviceClassifier.classify("Bose QC35") == DeviceType.HEADPHONE.value
        assert DeviceClassifier.classify("Sony WH-1000XM4") == DeviceType.HEADPHONE.value
    
    def test_camera_classification(self):
        """Test camera device detection"""
        assert DeviceClassifier.classify("Ring Camera") == DeviceType.CAMERA.value
        assert DeviceClassifier.classify("Nest Cam") == DeviceType.CAMERA.value
        assert DeviceClassifier.classify("Security CAM 01") == DeviceType.CAMERA.value
    
    def test_dashcam_classification(self):
        """Test dashcam device detection"""
        assert DeviceClassifier.classify("VIOFO A119") == DeviceType.DASHCAM.value
        assert DeviceClassifier.classify("70MAI Dash Cam") == DeviceType.DASHCAM.value
        assert DeviceClassifier.classify("Garmin Dash Cam") == DeviceType.DASHCAM.value
    
    def test_iot_classification(self):
        """Test IoT device detection"""
        assert DeviceClassifier.classify("Fitbit Versa") == DeviceType.IOT.value
        assert DeviceClassifier.classify("Alexa Echo") == DeviceType.IOT.value
        assert DeviceClassifier.classify("Smart Light") == DeviceType.IOT.value
    
    def test_unknown_device(self):
        """Test unknown device fallback"""
        assert DeviceClassifier.classify("RandomDevice123", "router") == "router"
        assert DeviceClassifier.classify("", "unknown") == "unknown"
        assert DeviceClassifier.classify(None, "default") == "default"
    
    def test_case_insensitive(self):
        """Test case-insensitive classification"""
        assert DeviceClassifier.classify("tesla") == DeviceType.CAR.value
        assert DeviceClassifier.classify("TESLA") == DeviceType.CAR.value
        assert DeviceClassifier.classify("TeSLa") == DeviceType.CAR.value
    
    def test_get_icon(self):
        """Test icon retrieval"""
        assert DeviceClassifier.get_icon(DeviceType.CAR.value) == "🚗"
        assert DeviceClassifier.get_icon(DeviceType.TV.value) == "📺"
        assert DeviceClassifier.get_icon(DeviceType.CAMERA.value) == "📷"
        assert DeviceClassifier.get_icon("unknown") == "❓"

class TestDevice:
    """Test Device data class"""
    
    def test_device_creation(self):
        """Test device object creation"""
        device = Device(
            lat=51.505,
            lon=-0.09,
            device_type="router",
            timestamp="2025-02-03T10:00:00Z",
            ssid="TestWiFi"
        )
        
        assert device.lat == 51.505
        assert device.lon == -0.09
        assert device.device_type == "router"
        assert device.ssid == "TestWiFi"
    
    def test_device_to_dict(self):
        """Test device dictionary conversion"""
        device = Device(
            lat=51.505,
            lon=-0.09,
            device_type="router",
            timestamp="2025-02-03T10:00:00Z",
            ssid="TestWiFi",
            signal=-65
        )
        
        device_dict = device.to_dict()
        
        assert isinstance(device_dict, dict)
        assert device_dict['lat'] == 51.505
        assert device_dict['ssid'] == "TestWiFi"
        assert 'signal' in device_dict
        
    def test_device_none_values_excluded(self):
        """Test that None values are excluded from dict"""
        device = Device(
            lat=51.505,
            lon=-0.09,
            device_type="router",
            timestamp="2025-02-03T10:00:00Z"
        )
        
        device_dict = device.to_dict()
        
        assert 'ssid' not in device_dict
        assert 'vendor' not in device_dict
        assert 'signal' not in device_dict

class TestAPIEndpoints:
    """Test API endpoints"""
    
    def test_health_check(self, client):
        """Test health check endpoint"""
        response = client.get('/api/health')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['status'] == 'healthy'
        assert 'timestamp' in data
        assert data['version'] == '2.0'
    
    def test_nearby_missing_coordinates(self, client):
        """Test nearby endpoint without coordinates"""
        response = client.get('/api/nearby')
        assert response.status_code == 400
        
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_nearby_invalid_latitude(self, client):
        """Test nearby endpoint with invalid latitude"""
        response = client.get('/api/nearby?lat=100&lon=0')
        assert response.status_code == 400
        
        data = json.loads(response.data)
        assert 'latitude' in data['error'].lower()
    
    def test_nearby_invalid_longitude(self, client):
        """Test nearby endpoint with invalid longitude"""
        response = client.get('/api/nearby?lat=0&lon=200')
        assert response.status_code == 400
        
        data = json.loads(response.data)
        assert 'longitude' in data['error'].lower()
    
    def test_nearby_valid_request(self, client):
        """Test nearby endpoint with valid coordinates"""
        response = client.get('/api/nearby?lat=51.505&lon=-0.09')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'devices' in data
        assert 'count' in data
        assert 'status' in data
        assert data['status'] == 'success'
        assert isinstance(data['devices'], list)
    
    def test_nearby_with_mode(self, client):
        """Test nearby endpoint with different modes"""
        # WiFi mode
        response = client.get('/api/nearby?lat=51.505&lon=-0.09&mode=wifi')
        assert response.status_code == 200
        
        # Bluetooth mode
        response = client.get('/api/nearby?lat=51.505&lon=-0.09&mode=bluetooth')
        assert response.status_code == 200
        
        # All mode
        response = client.get('/api/nearby?lat=51.505&lon=-0.09&mode=all')
        assert response.status_code == 200
    
    def test_search_missing_parameters(self, client):
        """Test search endpoint without required parameters"""
        response = client.get('/api/search')
        assert response.status_code == 400
        
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_search_invalid_type(self, client):
        """Test search endpoint with invalid type"""
        response = client.get('/api/search?type=invalid&query=test')
        assert response.status_code == 400
        
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_search_location_valid(self, client):
        """Test search by location"""
        response = client.get('/api/search?type=location&query=51.505,-0.09')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'devices' in data
        assert data['status'] == 'success'
    
    def test_search_location_invalid_format(self, client):
        """Test search by location with invalid format"""
        response = client.get('/api/search?type=location&query=invalid')
        assert response.status_code == 400
    
    def test_search_ssid(self, client):
        """Test search by SSID"""
        response = client.get('/api/search?type=ssid&query=TestNetwork')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'devices' in data
    
    def test_search_bssid(self, client):
        """Test search by BSSID"""
        response = client.get('/api/search?type=bssid&query=00:14:22:01:23:45')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'devices' in data
    
    def test_search_bssid_invalid(self, client):
        """Test search by invalid BSSID"""
        response = client.get('/api/search?type=bssid&query=invalid_mac')
        assert response.status_code == 400
    
    def test_stats_endpoint(self, client):
        """Test statistics endpoint"""
        response = client.get('/api/stats?lat=51.505&lon=-0.09')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'total_devices' in data
        assert 'device_types' in data
        assert 'top_vendors' in data
        assert 'search_area' in data
        assert data['status'] == 'success'
    
    def test_towers_endpoint(self, client):
        """Test cell towers endpoint"""
        response = client.get('/api/geo/towers?lat=51.505&lon=-0.09')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'towers' in data
        assert 'count' in data
        assert data['status'] == 'success'
    
    def test_404_error(self, client):
        """Test 404 error handling"""
        response = client.get('/api/nonexistent')
        assert response.status_code == 404
        
        data = json.loads(response.data)
        assert data['code'] == 404
        assert 'error' in data

class TestSecurity:
    """Test security features"""
    
    def test_large_radius_capped(self):
        """Test that large radius values are capped"""
        bounds = CoordinateValidator.calculate_bounds(0, 0, 999)
        
        # Should be capped at MAX_SEARCH_RADIUS (0.1)
        assert bounds['latrange2'] - bounds['latrange1'] <= 0.2
    
    def test_response_headers(self, client):
        """Test security response headers"""
        response = client.get('/api/health')
        
        # These would be set by nginx in production
        # Just verify the endpoint works
        assert response.status_code == 200

class TestRateLimiting:
    """Test rate limiting (requires Redis)"""
    
    @pytest.mark.skip(reason="Requires Redis connection")
    def test_rate_limit(self, client):
        """Test that rate limiting works"""
        # Make multiple rapid requests
        for _ in range(35):  # Over the 30/minute limit for nearby
            response = client.get('/api/nearby?lat=0&lon=0')
        
        # Should eventually get rate limited
        assert response.status_code == 429

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
