# Puebla Mapa — Distritos y Divisiones

Mapa interactivo de los 217 municipios de Puebla agrupados en **26 distritos** y **5 divisiones**.

## Instalación rápida

```bash
# 1. Dependencias
pip install -r requirements.txt

# 2. Base de datos
python manage.py migrate

# 3. Cargar datos (divisiones, distritos, 217 municipios)
#    También descarga el GeoJSON de INEGI (~30 s, sólo la primera vez)
python manage.py seed_data

# 4. Correr servidor
python manage.py runserver
```

Abre http://127.0.0.1:8000

## Admin Django

http://127.0.0.1:8000/admin  
Usuario: `admin` · Contraseña: `admin123`

Desde el admin puedes:
- Reasignar municipios a otro distrito
- Cambiar los colores de cada división
- Renombrar distritos y divisiones

## Reasignaciones por script

```python
# Reasignar un municipio a otro distrito
from mapa.models import Municipio, Distrito
m = Municipio.objects.get(nombre='Atlixco')
m.distrito = Distrito.objects.get(numero=5)
m.save()

# Reasignar todos los municipios de un distrito a otro
Municipio.objects.filter(distrito__numero=3).update(
    distrito=Distrito.objects.get(numero=7)
)
```

Después de cualquier cambio, limpia la caché:
```python
from django.core.cache import cache
cache.delete('puebla_geojson_enriquecido')
```

## GeoJSON manual (si INEGI falla)

Descarga el GeoJSON de municipios de Puebla y guárdalo en:
```
mapa/data/puebla_municipios.geojson
```

La propiedad `CVE_MUN` debe ser de 3 dígitos (`001`–`217`).

## Estructura

```
puebla_mapa/
├── mapa/
│   ├── models.py          # División, Distrito, Municipio
│   ├── views.py           # index + /api/geojson/ + /api/divisiones/
│   ├── admin.py           # Admin con inline de municipios
│   ├── data/              # GeoJSON local (generado por seed_data)
│   └── management/commands/seed_data.py
└── puebla_mapa/
    ├── settings.py
    └── urls.py
```
