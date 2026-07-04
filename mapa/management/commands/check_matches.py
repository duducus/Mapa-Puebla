"""
check_matches.py
Compara el GeoJSON local con la BD y reporta qué features no encuentran municipio.
Corre con: python manage.py check_matches
"""
import json, os, unicodedata
from django.core.management.base import BaseCommand
from mapa.models import Municipio

GEOJSON_LOCAL = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    'data', 'puebla_municipios.geojson'
)

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


class Command(BaseCommand):
    help = 'Reporta municipios del GeoJSON que no hacen match con la BD'

    def handle(self, *args, **options):
        if not os.path.exists(GEOJSON_LOCAL):
            self.stdout.write(self.style.ERROR(f'No existe: {GEOJSON_LOCAL}'))
            return

        by_cve  = {m.cve_mun: m        for m in Municipio.objects.all()}
        by_name = {_norm(m.nombre): m   for m in Municipio.objects.all()}

        with open(GEOJSON_LOCAL, encoding='utf-8') as f:
            raw = json.load(f)

        ok, wrong_cve, no_match = [], [], []

        for feat in raw.get('features', []):
            props    = feat['properties']
            name_raw = (props.get('NOM_MUN') or props.get('NAME_2') or
                        props.get('NOMGEO') or '').strip()
            cve_val  = _cve(props)
            name_key = _norm(name_raw) if name_raw else ''

            # ¿CVE existe pero con nombre distinto?
            cve_mun = by_cve.get(cve_val)
            if cve_mun and name_raw and _norm(cve_mun.nombre) != name_key:
                wrong_cve.append((name_raw, cve_val, cve_mun.nombre))

            # ¿Match final?
            if name_key and name_key in by_name:
                ok.append(name_raw)
            elif cve_val and cve_val in by_cve and (
                    not name_raw or _norm(by_cve[cve_val].nombre) == name_key):
                ok.append(name_raw or cve_val)
            else:
                no_match.append((name_raw, cve_val))

        self.stdout.write(f'\n✔ Con match:      {len(ok)}')
        self.stdout.write(f'⚠  CVE incorrecto: {len(wrong_cve)}  (el nombre es la clave real)')
        self.stdout.write(f'✗ Sin match:       {len(no_match)}\n')

        if no_match:
            self.stdout.write(self.style.WARNING('── NOMBRES SIN MATCH (copiar para alias) ──'))
            for name, cve in sorted(no_match):
                # Buscar el más parecido en la BD
                best, best_score = None, 0
                for db_key, m in by_name.items():
                    common = len(set(name_key.split()) & set(db_key.split()))
                    if common > best_score:
                        best, best_score = m.nombre, common
                sugg = f'  → ¿"{best}"?' if best and best_score > 0 else ''
                self.stdout.write(f'  GeoJSON: {name!r:40}  CVE:{cve}{sugg}')

        if wrong_cve:
            self.stdout.write(self.style.WARNING('\n── CVE INCORRECTOS (GADM ≠ INEGI) ──'))
            for name, cve, db_nombre in wrong_cve[:10]:
                self.stdout.write(f'  GeoJSON nombre: {name!r}')
                self.stdout.write(f'  CVE {cve} en BD apunta a: {db_nombre!r}')
