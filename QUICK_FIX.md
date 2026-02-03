# 🔧 Solución: Error "Resource not found"

## El Problema

El error `"error": "Resource not found"` ocurre porque Flask no encuentra los archivos HTML (templates) necesarios.

## ✅ Solución Rápida

### 1. Crear la estructura de carpetas

```bash
mkdir -p templates static/css static/js
```

### 2. Colocar los archivos HTML

He creado dos templates que necesitas:

- **`templates/index.html`** - Página principal con información de la API
- **`templates/wifi-search.html`** - Mapa interactivo para búsqueda de dispositivos

### 3. Estructura correcta del proyecto

```
tu-proyecto/
├── app.py                      # Aplicación Flask
├── requirements.txt            # Dependencias
├── .env                        # Credenciales (crear desde .env.example)
├── templates/                  # ← IMPORTANTE
│   ├── index.html             # Página principal
│   └── wifi-search.html       # Mapa interactivo
├── static/                     # Archivos estáticos (opcional)
│   ├── css/
│   └── js/
└── ...otros archivos
```

## 🚀 Pasos para Ejecutar

### Opción 1: Ejecución Directa

```bash
# 1. Asegúrate de tener la estructura correcta
ls templates/
# Debe mostrar: index.html  wifi-search.html

# 2. Configura las variables de entorno
cp .env.example .env
nano .env  # Edita con tus API keys

# 3. Instala dependencias (si no lo has hecho)
pip install -r requirements.txt

# 4. Inicia Redis (en otra terminal)
redis-server

# 5. Ejecuta la aplicación
python app.py
```

### Opción 2: Con Docker (Recomendado)

```bash
# 1. Asegúrate de tener docker-compose.yml
# 2. Configura .env
cp .env.example .env
nano .env

# 3. Inicia todo con un comando
docker-compose up -d

# 4. Ver logs
docker-compose logs -f app
```

## 🌐 URLs Disponibles

Después de iniciar la aplicación:

| URL | Descripción |
|-----|-------------|
| `http://localhost:8080/` | Página principal con información |
| `http://localhost:8080/map` | Mapa interactivo (lo que necesitas) |
| `http://localhost:8080/api/health` | Health check |
| `http://localhost:8080/api/nearby?lat=18.4861&lon=-69.9312` | API de dispositivos cercanos |

## 🎯 Acceso al Mapa

La ruta correcta para el mapa interactivo es:

```
http://localhost:8080/map
```

O si estás usando la URL que mostraste:

```
http://127.0.0.1:8080/map-w
```

**Nota:** En el código mejorado, la ruta es `/map`, pero puedes cambiarla en `app.py`:

```python
@app.route('/map-w')  # Cambiar de /map a /map-w si lo prefieres
def wifi_map():
    return render_template('wifi-search.html')
```

## 🔍 Verificar que Todo Funciona

### Test 1: Health Check
```bash
curl http://localhost:8080/api/health
```

**Respuesta esperada:**
```json
{
  "status": "healthy",
  "timestamp": "2025-02-03T...",
  "version": "2.0"
}
```

### Test 2: Página Principal
```bash
curl http://localhost:8080/
```

Debe devolver HTML, no un error.

### Test 3: Mapa Interactivo
```bash
curl http://localhost:8080/map
```

Debe devolver HTML con Leaflet maps.

## ❌ Errores Comunes y Soluciones

### Error: "Resource not found"
**Causa:** Falta la carpeta `templates/` o los archivos HTML
**Solución:** Crear la carpeta y copiar los archivos HTML

### Error: "TemplateNotFound: wifi-search.html"
**Causa:** El archivo no está en `templates/`
**Solución:** 
```bash
ls templates/wifi-search.html
# Si no existe, copiarlo ahí
```

### Error: "ModuleNotFoundError: No module named 'flask'"
**Causa:** Dependencias no instaladas
**Solución:**
```bash
pip install -r requirements.txt
```

### Error: "Connection refused" al buscar dispositivos
**Causa:** Redis no está corriendo
**Solución:**
```bash
# Iniciar Redis
redis-server

# O con Docker:
docker-compose up redis -d
```

### Error: API keys inválidas
**Causa:** `.env` no configurado o keys incorrectas
**Solución:**
```bash
# Editar .env con tus keys reales
nano .env
```

## 📝 Configuración de API Keys

Necesitas obtener keys de:

### WiGLE (WiFi/Bluetooth)
1. Registrarse en https://wigle.net/account
2. Ir a "Account" → "API Token"
3. Copiar API Name y Token

### OpenCellID (Torres celulares)
1. Registrarse en https://opencellid.org/
2. Obtener API key
3. O usar UnwiredLabs: https://unwiredlabs.com/

### Shodan (Opcional - IoT)
1. Registrarse en https://shodan.io/
2. Ir a "Account" → "API Key"

## 🎨 Características del Mapa Interactivo

Una vez funcionando, el mapa incluye:

- 🗺️ **Mapa interactivo** con Leaflet/OpenStreetMap
- 🔍 **3 modos de búsqueda**: WiFi, Bluetooth, Todo
- 📍 **Geolocalización**: "Usar Mi Ubicación"
- 📊 **Estadísticas en tiempo real**
- 🎯 **Marcadores personalizados** con emojis
- 💬 **Popups informativos** con detalles del dispositivo
- 🎨 **Leyenda** de tipos de dispositivos

## 📞 Si Aún No Funciona

1. Verifica que todos los archivos estén en su lugar:
```bash
ls -la templates/
ls -la app.py
```

2. Verifica que Flask esté corriendo:
```bash
ps aux | grep python
```

3. Revisa los logs:
```bash
# Si usas Docker:
docker-compose logs -f app

# Si corres directamente:
# Los logs aparecerán en la terminal donde ejecutaste python app.py
```

4. Prueba el endpoint directo:
```bash
curl -v http://localhost:8080/map
```

## 🎉 ¡Listo!

Ahora deberías poder:
1. Visitar `http://localhost:8080/map`
2. Ver el mapa interactivo
3. Buscar dispositivos WiFi, Bluetooth y torres celulares
4. Ver estadísticas en tiempo real

---

**💡 Tip:** Si estás en desarrollo, puedes activar el modo debug en `.env`:
```
FLASK_ENV=development
```

Esto te dará más información sobre cualquier error.
