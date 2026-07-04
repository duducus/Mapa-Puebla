import json, os, unicodedata
from django.shortcuts import render
from django.http import JsonResponse
from django.core.cache import cache
from .models import Municipio

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
                'municipios_distrito': sorted(dist_muns.get(d.id, [])),
                'mun_nombre':          m.nombre,
            })
        else:
            props.update({
                'distrito_numero':     None,
                'distrito_nombre':     'Sin asignar',
                'distrito_color':      '#2a2a2a',
                'municipios_distrito': [],
                'mun_nombre': (props.get('NOM_MUN') or props.get('NAME_2')
                               or props.get('NOMGEO') or '?'),
            })

    result = json.dumps(raw, ensure_ascii=False)
    cache.set('puebla_geojson_v6', result, 60 * 30)
    return JsonResponse(raw, safe=False)

def distritos_api(request):
    from .models import Distrito
    return JsonResponse([
        {'numero': d.numero, 'nombre': d.nombre, 'color': COLORES.get(d.numero, '#888')}
        for d in Distrito.objects.order_by('numero')
        if d.municipios.exists()
    ], safe=False)
