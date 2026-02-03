# 🗺️ Advanced Network Mapper v2.0

A professional-grade network device mapping application that tracks WiFi networks, Bluetooth devices, cell towers, and IoT devices using multiple APIs (WiGLE, OpenCellID, Shodan).

## ✨ Features

### Core Functionality
- 🌐 **WiFi Network Mapping**: Search and track WiFi access points
- 📶 **Bluetooth Device Detection**: Discover nearby Bluetooth devices
- 🗼 **Cell Tower Mapping**: Locate cellular infrastructure
- 💡 **IoT Device Discovery**: Find Internet-connected devices
- 🚗 **Smart Classification**: Automatic device type detection (cars, TVs, cameras, etc.)

### Advanced Features
- ⚡ **Redis Caching**: Fast response times with intelligent caching
- 🛡️ **Rate Limiting**: Protection against API abuse
- 🔐 **Security First**: Environment-based configuration, input validation
- 📊 **Statistics API**: Get insights about device distribution
- 🐳 **Docker Support**: Easy deployment with Docker Compose
- 📝 **Comprehensive Logging**: Detailed application logs
- 🔍 **Advanced Search**: Search by location, SSID, BSSID, or IP
- 🎯 **Device Icons**: Visual representation of device types

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Redis server
- API keys from:
  - [WiGLE](https://wigle.net/account) (WiFi/Bluetooth data)
  - [OpenCellID](https://opencellid.org/) (Cell tower data)
  - [Shodan](https://shodan.io/) (IoT device data - optional)

### Installation

#### Option 1: Docker (Recommended)

```bash
# Clone the repository
git clone <your-repo-url>
cd network-mapper

# Copy environment file
cp .env.example .env

# Edit .env with your API keys
nano .env

# Start with Docker Compose
docker-compose up -d

# Check logs
docker-compose logs -f app
```

The application will be available at `http://localhost:80`

#### Option 2: Manual Installation

```bash
# Clone the repository
git clone <your-repo-url>
cd network-mapper

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy and configure environment
cp .env.example .env
nano .env  # Add your API keys

# Start Redis (in another terminal)
redis-server

# Run the application
python app.py
```

The application will be available at `http://localhost:8080`

## 📚 API Documentation

### Base URL
```
http://localhost:8080/api
```

### Endpoints

#### 1. Health Check
```http
GET /api/health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-02-03T10:00:00.000000Z",
  "version": "2.0"
}
```

#### 2. Nearby Devices
Search for devices near a location.

```http
GET /api/nearby?lat=51.505&lon=-0.09&mode=wifi&radius=0.01
```

**Parameters:**
- `lat` (required): Latitude (-90 to 90)
- `lon` (required): Longitude (-180 to 180)
- `mode` (optional): `wifi`, `bluetooth`, or `all` (default: `wifi`)
- `radius` (optional): Search radius in degrees (default: 0.01, max: 0.1)

**Response:**
```json
{
  "devices": [
    {
      "lat": 51.505,
      "lon": -0.09,
      "ssid": "CoffeeShop_WiFi",
      "bssid": "00:14:22:01:23:45",
      "vendor": "Cisco Systems",
      "signal": -65,
      "timestamp": "2025-02-03T10:00:00Z",
      "device_type": "router",
      "icon": "📡"
    }
  ],
  "count": 1,
  "timestamp": "2025-02-03T10:00:00.000000Z",
  "status": "success"
}
```

#### 3. Advanced Search
Search by various criteria.

```http
GET /api/search?type=ssid&query=CoffeeShop
```

**Parameters:**
- `type` (required): `location`, `ssid`, `bssid`, or `network`
- `query` (required): Search query
  - For `location`: "lat,lon" (e.g., "51.505,-0.09")
  - For `ssid`: Network name
  - For `bssid`: MAC address (e.g., "00:14:22:01:23:45")
  - For `network`: IP address or query

**Response:** Same format as `/api/nearby`

#### 4. Statistics
Get device statistics for an area.

```http
GET /api/stats?lat=51.505&lon=-0.09&radius=0.05
```

**Response:**
```json
{
  "total_devices": 150,
  "device_types": {
    "router": 80,
    "cell_tower": 45,
    "car": 15,
    "camera": 10
  },
  "top_vendors": {
    "Cisco Systems": 25,
    "Apple Inc": 20,
    "Samsung": 15
  },
  "average_signal": -72.5,
  "search_area": {
    "center": {"lat": 51.505, "lon": -0.09},
    "radius_km": 5.55
  },
  "timestamp": "2025-02-03T10:00:00.000000Z",
  "status": "success"
}
```

#### 5. Cell Towers
Get cell towers in an area.

```http
GET /api/geo/towers?lat=51.505&lon=-0.09
```

**Response:**
```json
{
  "towers": [
    {
      "lat": 51.505,
      "lon": -0.09,
      "cell_id": "123456",
      "signal": -85,
      "device_type": "cell_tower",
      "vendor": "LTE Tower",
      "icon": "🗼"
    }
  ],
  "count": 1,
  "timestamp": "2025-02-03T10:00:00.000000Z",
  "status": "success"
}
```

### Rate Limits

| Endpoint | Rate Limit |
|----------|-----------|
| `/api/nearby` | 30 requests/minute |
| `/api/search` | 20 requests/minute |
| `/api/stats` | 10 requests/minute |
| `/api/geo/towers` | 20 requests/minute |
| Global | 200 requests/day, 50 requests/hour |

### Error Responses

All errors follow this format:
```json
{
  "error": "Error message",
  "status": "error",
  "code": 400
}
```

**Status Codes:**
- `400`: Bad Request (invalid parameters)
- `401`: Unauthorized (invalid API key)
- `404`: Not Found
- `429`: Rate Limit Exceeded
- `500`: Internal Server Error

## 🔧 Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `WIGLE_API_NAME` | Yes | WiGLE API username |
| `WIGLE_API_TOKEN` | Yes | WiGLE API token |
| `OPENCELLID_API_KEY` | Yes | OpenCellID API key |
| `SHODAN_API_KEY` | No | Shodan API key (optional) |
| `SECRET_KEY` | Yes | Flask secret key |
| `REDIS_URL` | No | Redis connection URL (default: redis://localhost:6379/0) |
| `FLASK_ENV` | No | Environment (development/production) |
| `PORT` | No | Server port (default: 8080) |
| `APP_API_KEY` | No | Optional API key for protected endpoints |

### Device Classification

The system automatically classifies devices into categories:

| Type | Keywords | Icon |
|------|----------|------|
| Car | TESLA, FORD, BMW, TOYOTA, etc. | 🚗 |
| TV | SAMSUNG, LG, ROKU, BRAVIA, etc. | 📺 |
| Headphone | BOSE, AIRPOD, BEATS, SONY, etc. | 🎧 |
| Camera | RING, NEST, ARLO, HIKVISION, etc. | 📷 |
| Dashcam | VIOFO, NEXTBASE, GARMIN DASH, etc. | 📹 |
| IoT | FITBIT, ALEXA, SMART, etc. | 💡 |
| Router | Default WiFi networks | 📡 |
| Cell Tower | Cellular infrastructure | 🗼 |
| Bluetooth | Generic Bluetooth devices | 📶 |

## 🐳 Docker Deployment

### Production Deployment

```bash
# Build and start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Rebuild after changes
docker-compose up -d --build
```

### Services

The Docker Compose stack includes:
- **app**: Flask application (port 8080)
- **redis**: Redis cache (port 6379)
- **nginx**: Reverse proxy (ports 80/443)

## 🧪 Testing

```bash
# Activate virtual environment
source venv/bin/activate

# Run tests
pytest tests/

# Test API connections
flask test-apis

# Check code style
black app.py --check
flake8 app.py
```

## 📊 Monitoring

### Application Logs

```bash
# Docker logs
docker-compose logs -f app

# Direct logs
tail -f logs/app.log
```

### Health Check

```bash
curl http://localhost:8080/api/health
```

### Redis Monitoring

```bash
# Connect to Redis CLI
docker-compose exec redis redis-cli

# Check cache keys
KEYS *

# Monitor commands
MONITOR
```

## 🔒 Security Best Practices

1. **Never commit `.env` file** - Add it to `.gitignore`
2. **Use strong SECRET_KEY** - Generate with `openssl rand -hex 32`
3. **Enable HTTPS** - Use Let's Encrypt or your SSL certificate
4. **Set APP_API_KEY** - Protect sensitive endpoints
5. **Keep dependencies updated** - Run `pip list --outdated`
6. **Monitor logs** - Set up log aggregation
7. **Configure firewall** - Restrict Redis access
8. **Use Docker secrets** - For production deployments

## 📈 Performance Optimization

### Caching Strategy

- **WiFi/Bluetooth searches**: 5 minutes
- **Cell tower data**: 10 minutes
- **Shodan results**: 10 minutes

### Rate Limiting

Configure in `app.py`:
```python
@limiter.limit("30 per minute")
def nearby():
    # ...
```

### Redis Memory

Configure in `docker-compose.yml`:
```yaml
command: redis-server --maxmemory 256mb --maxmemory-policy allkeys-lru
```

## 🐛 Troubleshooting

### Common Issues

**Issue: "Invalid or missing API key"**
```bash
# Check your .env file
cat .env | grep API

# Verify API keys are valid
flask test-apis
```

**Issue: "Connection refused to Redis"**
```bash
# Check Redis is running
docker-compose ps redis

# Test Redis connection
redis-cli ping
```

**Issue: "Rate limit exceeded"**
```bash
# Check Redis for rate limit keys
redis-cli KEYS "LIMITER*"

# Clear rate limits (development only!)
redis-cli FLUSHALL
```

**Issue: "No devices found"**
- Verify API credentials are correct
- Check API rate limits on provider sites
- Try different coordinates
- Check application logs for API errors

## 📝 Development

### Project Structure

```
network-mapper/
├── app.py                 # Main application
├── requirements.txt       # Python dependencies
├── Dockerfile            # Docker configuration
├── docker-compose.yml    # Docker Compose setup
├── nginx.conf           # Nginx configuration
├── .env.example         # Environment template
├── README.md            # This file
├── templates/           # HTML templates
│   ├── index.html
│   └── wifi-search.html
├── static/             # Static assets
│   ├── css/
│   ├── js/
│   └── img/
└── tests/              # Test suite
    ├── test_api.py
    └── test_classification.py
```

### Adding New Device Types

Edit `DEVICE_PATTERNS` in `app.py`:

```python
DEVICE_PATTERNS = {
    DeviceType.YOUR_TYPE: [
        "KEYWORD1", "KEYWORD2", "KEYWORD3"
    ],
    # ...
}
```

### Custom API Clients

Create a new class inheriting from `APIClient`:

```python
class YourAPI(APIClient):
    def __init__(self):
        super().__init__('https://api.example.com')
    
    def search(self, lat, lon):
        # Implementation
        pass
```

## 📄 License

This project is licensed under the MIT License.

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📧 Support

For issues and questions:
- Open an issue on GitHub
- Check the troubleshooting section
- Review API provider documentation

## 🙏 Acknowledgments

- [WiGLE](https://wigle.net/) - WiFi and Bluetooth data
- [OpenCellID](https://opencellid.org/) - Cell tower database
- [Shodan](https://shodan.io/) - IoT device search
- Flask community for excellent documentation

## 🔄 Version History

### v2.0 (Current)
- ✨ Complete rewrite with professional architecture
- 🔒 Enhanced security features
- ⚡ Redis caching implementation
- 🛡️ Rate limiting
- 🐳 Docker support
- 📊 Statistics endpoint
- 🎯 Smart device classification
- 📝 Comprehensive documentation

### v1.0
- Basic functionality
- Simple API integration
- Minimal error handling

---

**Made with ❤️ for network security enthusiasts**
