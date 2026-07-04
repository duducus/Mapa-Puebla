import json, os, unicodedata
from django.shortcuts import render
from django.http import JsonResponse
from django.core.cache import cache
from .models import Distrito, Municipio

GEOJSON_LOCAL = os.path.join(os.path.dirname(__file__), 'data', 'puebla_municipios.geojson')

COLORES = {
     1:'#E74C3C',  2:'#FF8C00',  3:'#F1C40F',  4:'#2ECC71',
     5:'#1ABC9C',  6:'#3498DB',  7:'#9B59B6',  8:'#E91E63',
     9:'#FF5722', 10:'#00BCD4', 11:'#8BC34A', 12:'#FF9800',
    13:'#03A9F4', 14:'#C2185B', 15:'#CDDC39', 16:'#26C6DA',
    17:'#AB47BC', 18:'#66BB6A', 19:'#FFA726', 20:'#42A5F5',
    21:'#EF5350', 22:'#26A69A', 23:'#D4E157', 24:'#7E57C2',
    25:'#EC407A', 26:'#29B6F6',
}

ZONAS_GEOGRAFICAS = {
    'Región Norte': [1, 2, 3, 4, 5, 6, 13, 14, 15],
    'Puebla Centro': [7, 8, 9, 10, 11, 12, 16, 17, 18, 19, 20],
    'Región Sur': [21, 22, 23, 24, 25, 26],
}

COLORES_ZONA = {
    'Región Norte': '#2f80ed',
    'Puebla Centro': '#d12f7a',
    'Región Sur': '#27ae60',
    'Sin zona': '#667085',
}

DETALLES_DISTRITO = {
    7: {
        'municipios_ppt': [
            'Tlahuapan',
            'San Matías Tlalancaleca',
            'San Salvador el Verde',
            'San Martín Texmelucan de Labastida',
            'San Felipe Teotlalcingo',
        ],
    },
    8: {
        'municipios_ppt': [
            'Chiautzingo',
            'Huejotzingo',
            'Tlaltenango',
            'San Miguel Xoxtla',
            'Coronango',
            'Domingo Arenas',
            'Juan C. Bonilla',
            'Calpan',
        ],
    },
    9: {
        'municipios_ppt': ['Cuautlancingo', 'H. Puebla de Zaragoza'],
        'notas': ['Incluye actualización de cartografía electoral con secciones eliminadas y secciones creadas.'],
    },
    10: {
        'municipios_ppt': ['H. Puebla de Zaragoza'],
        'notas': ['Forma parte del grupo urbano de distritos 10, 11, 16, 17, 19 y 20.'],
    },
    11: {
        'municipios_ppt': ['H. Puebla de Zaragoza'],
        'notas': ['Incluye actualización de cartografía electoral con secciones eliminadas y secciones creadas.'],
    },
    12: {
        'municipios_ppt': [
            'Tepatlaxco de Hidalgo',
            'Acajete',
            'Amozoc',
            'Cuautinchán',
            'Tecali de Herrera',
            'H. Puebla de Zaragoza',
        ],
        'notas': ['Incluye actualización de cartografía electoral con secciones eliminadas y secciones creadas.'],
    },
    16: {
        'municipios_ppt': ['H. Puebla de Zaragoza'],
        'notas': ['Incluye actualización de cartografía electoral con secciones eliminadas y secciones creadas.'],
    },
    17: {
        'municipios_ppt': ['H. Puebla de Zaragoza'],
        'notas': ['Forma parte del grupo urbano de distritos 10, 11, 16, 17, 19 y 20.'],
    },
    18: {
        'municipios_ppt': ['San Andrés Cholula', 'San Pedro Cholula'],
        'notas': ['Incluye actualización de cartografía electoral con secciones eliminadas y secciones creadas.'],
    },
    19: {
        'municipios_ppt': ['H. Puebla de Zaragoza'],
        'notas': ['Forma parte del grupo urbano de distritos 10, 11, 16, 17, 19 y 20.'],
    },
    20: {
        'municipios_ppt': ['H. Puebla de Zaragoza'],
        'notas': ['Incluye actualización de cartografía electoral con secciones eliminadas y secciones creadas.'],
    },
}

FUENTE_DISTRITACION = (
    'Elaboración propia con información del Estadístico de Padrón Electoral y Lista Nominal '
    'de Electores del Estado de Puebla. Corte al 31 de mayo de 2026.'
)


def _zona_distrito(numero):
    for zona, numeros in ZONAS_GEOGRAFICAS.items():
        if numero in numeros:
            return zona
    return 'Sin zona'


def _detalle_distrito(distrito):
    detalle = DETALLES_DISTRITO.get(distrito.numero, {})
    municipios = list(distrito.municipios.order_by('nombre').values_list('nombre', flat=True))
    return {
        'numero': distrito.numero,
        'nombre': distrito.nombre,
        'division': distrito.division.nombre if distrito.division else '',
        'zona': _zona_distrito(distrito.numero),
        'zona_color': COLORES_ZONA.get(_zona_distrito(distrito.numero), '#667085'),
        'color': COLORES.get(distrito.numero, '#888'),
        'municipios': municipios,
        'municipios_ppt': detalle.get('municipios_ppt', municipios),
        'notas': detalle.get('notas', []),
        'fuente': FUENTE_DISTRITACION,
        'imagen': f'/static/mapa/distritos/dtto-{distrito.numero}.jfif',
    }

def _norm(s):
    s = s.upper()
    s = ''.join(c for c in unicodedata.normalize('NFD', s)
                if unicodedata.category(c) != 'Mn')
    s = ''.join(c if c.isalnum() or c == ' ' else ' ' for c in s)
    return ' '.join(s.split())

def _cve(props):
    cve = props.get('CVE_MUN', '')
    if not cve:
        cve = props.get('CVEGEO', '')[-3:]
    return str(cve).zfill(3) if cve else ''

def index(request):
    return render(request, 'mapa/index.html')

def geojson_api(request):
    cached = cache.get('puebla_geojson_v6')
    if cached:
        return JsonResponse(json.loads(cached), safe=False)

    if not os.path.exists(GEOJSON_LOCAL):
        return JsonResponse(
            {'error': 'GeoJSON no encontrado. Corre: python manage.py seed_data'},
            status=503)

    with open(GEOJSON_LOCAL, encoding='utf-8') as f:
        raw = json.load(f)

    all_muns = list(Municipio.objects.select_related('distrito').all())

    # Tres lookups para cubrir todos los casos:
    by_cve     = {m.cve_mun:                        m for m in all_muns}
    by_name    = {_norm(m.nombre):                   m for m in all_muns}
    # GADM concatena palabras en CamelCase → comparar sin espacios
    by_name_ns = {_norm(m.nombre).replace(' ', ''):  m for m in all_muns}

    def find(props):
        name_raw = (props.get('NOM_MUN') or props.get('NAME_2')
                    or props.get('NOMGEO') or '').strip()
        cve_val  = _cve(props)

        # 1. CVE — validar con nombre para evitar mismatch GADM vs INEGI
        if cve_val:
            m = by_cve.get(cve_val)
            if m:
                if not name_raw or _norm(m.nombre) == _norm(name_raw):
                    return m  # CVE correcto confirmado por nombre

        # 2. Nombre exacto (normalizado)
        if name_raw:
            m = by_name.get(_norm(name_raw))
            if m:
                return m

        # 3. Sin espacios — resuelve CamelCase de GADM
        #    "SanMartínTexmelucan" → "SANMARTINTEXMELUCAN"
        #    "San Martín Texmelucan" → "SANMARTINTEXMELUCAN"  ✓
        if name_raw:
            m = by_name_ns.get(_norm(name_raw).replace(' ', ''))
            if m:
                return m

        return None

    # Municipios por distrito (sidebar)
    dist_muns = {}
    for feat in raw.get('features', []):
        m = find(feat['properties'])
        if m and m.distrito_id:
            dist_muns.setdefault(m.distrito_id, []).append(m.nombre)

    # Enriquecer features
    for feat in raw.get('features', []):
        props = feat['properties']
        m = find(props)
        if m and m.distrito:
            d = m.distrito
            props.update({
                'distrito_numero':     d.numero,
                'distrito_nombre':     d.nombre,
                'distrito_color':      COLORES.get(d.numero, '#888'),
                'distrito_zona':       _zona_distrito(d.numero),
                'zona_color':          COLORES_ZONA.get(_zona_distrito(d.numero), '#667085'),
                'division_nombre':     d.division.nombre if d.division else '',
                'municipios_distrito': sorted(dist_muns.get(d.id, [])),
                'mun_nombre':          m.nombre,
            })
        else:
            props.update({
                'distrito_numero':     None,
                'distrito_nombre':     'Sin asignar',
                'distrito_color':      '#2a2a2a',
                'distrito_zona':       'Sin zona',
                'zona_color':          COLORES_ZONA['Sin zona'],
                'division_nombre':     '',
                'municipios_distrito': [],
                'mun_nombre': (props.get('NOM_MUN') or props.get('NAME_2')
                               or props.get('NOMGEO') or '?'),
            })

    result = json.dumps(raw, ensure_ascii=False)
    cache.set('puebla_geojson_v6', result, 60 * 30)
    return JsonResponse(raw, safe=False)

def distritos_api(request):
    return JsonResponse([
        _detalle_distrito(d)
        for d in Distrito.objects.select_related('division').prefetch_related('municipios').order_by('numero')
    ], safe=False)
