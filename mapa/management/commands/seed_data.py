"""
seed_data.py — Distritación electoral local oficial de Puebla
Fuente: INE - Descriptivo de la Distritación 2017 (CG1ex201707-20-ap-2-2-a3.pdf)
26 distritos locales, 217 municipios, 5 divisiones geográficas.
"""
import json, os, unicodedata
from django.core.management.base import BaseCommand
from django.core.cache import cache
from mapa.models import Division, Distrito, Municipio

# ── 5 Divisiones geográficas (num. de distrito → división) ───────────────────
DIVISIONES = {
    'Sierra Norte': ('#2980B9', [1, 2, 3, 4, 5, 6]),
    'Valle Puebla': ('#27AE60', [7, 8, 12, 13, 18, 21]),
    'Zona Metro':   ('#C0392B', [9, 10, 11, 16, 17, 19, 20]),
    'Oriente':      ('#E67E22', [14, 15]),
    'Sur':          ('#8E44AD', [22, 23, 24, 25, 26]),
}

# ── Cabeceras distritales (fuente: INE) ───────────────────────────────────────
CABECERAS = {
     1:'Xicotepec de Juárez',  2:'Huauchinango',
     3:'Zacatlán',             4:'Zacapoaxtla',
     5:'Tlatlauquitepec',      6:'Teziutlán',
     7:'San Martín Texmelucan',8:'Huejotzingo',
     9:'Puebla',              10:'Puebla',
    11:'Puebla',              12:'Amozoc',
    13:'Tepeaca',             14:'Ciudad Serdán',
    15:'Tecamachalco',        16:'Puebla',
    17:'Puebla',              18:'San Pedro Cholula',
    19:'Puebla',              20:'Puebla',
    21:'Atlixco',             22:'Izúcar de Matamoros',
    23:'Acatlán de Osorio',   24:'Tehuacán',
    25:'Tehuacán',            26:'Ajalpan',
}

# ── Municipios por distrito (INE, descriptivo oficial 2017) ───────────────────
# Puebla (ciudad) aparece en D9,10,11,12,16,17,19,20 → se asigna al D9
# Tehuacán aparece en D24 y D25 → se asigna al D24
MUNS_POR_DISTRITO = {
    1:  ['HONEY','FRANCISCO Z MENA','JALPAN','NAUPAN','PAHUATLAN','PANTEPEC',
         'TLACUILOTEPEC','TLAXCO','VENUSTIANO CARRANZA','XICOTEPEC'],
    2:  ['AHUACATLAN','AMIXTLAN','CAMOCUAUTLA','COATEPEC','CHICONCUAUTLA',
         'HERMENEGILDO GALEANA','HUAUCHINANGO','JOPALA','JUAN GALINDO',
         'SAN FELIPE TEPATLAN','TEPANGO DE RODRIGUEZ','TLAOLA','TLAPACOYA',
         'ZIHUATEUTLA'],
    3:  ['AHUAZOTEPEC','AQUIXTLA','CHIGNAHUAPAN','IXTACAMAXTITLAN',
         'LIBRES','OCOTEPEC','ZACATLAN'],
    4:  ['CAXHUACAN','CUAUTEMPAN','HUEHUETLA','HUEYTLALPAN',
         'HUITZILAN DE SERDAN','ATLEQUIZAYAN','IXTEPEC','NAUZONTLA','OLINTLA',
         'TEPETZINTLA','TETELA DE OCAMPO','XOCHIAPULCO',
         'XOCHITLAN DE VICENTE SUAREZ','ZACAPOAXTLA','ZAPOTITLAN DE MENDEZ',
         'ZARAGOZA','ZAUTLA','ZONGOZOTLA'],
    5:  ['ACATENO','ATEMPAN','AYOTOXCO DE GUERRERO','CUETZALAN DEL PROGRESO',
         'HUEYAPAN','HUEYTAMALCO','JONOTLA','TENAMPULCO',
         'TETELES DE AVILA CASTILLO','TLATLAUQUITEPEC','TUZAMAPAN DE GALEANA',
         'YAONAHUAC','ZOQUIAPAN'],
    6:  ['CUYOACO','CHIGNAUTLA','GUADALUPE VICTORIA','LAFRAGUA',
         'TEPEYAHUALCO','TEZIUTLAN','XIUTETELCO'],
    7:  ['SAN MARTIN TEXMELUCAN','SAN MATIAS TLALANCALECA',
         'SAN SALVADOR EL VERDE','TLAHUAPAN'],
    8:  ['CALPAN','CORONANDO','CORONANGO','CHIAUTZINGO','DOMINGO ARENAS',
         'HUEJOTZINGO','JUAN C BONILLA','NEALTICAN','SAN FELIPE TEOTLALCINGO',
         'SAN MIGUEL XOXTLA','SAN NICOLAS DE LOS RANCHOS','TLALTENANGO'],
    9:  ['CUAUTLANCINGO','PUEBLA'],      # Puebla en 8 distritos → D9
    10: [], 11: [], 16: [], 17: [], 19: [], 20: [],
    12: ['ACAJETE','AMOZOC','ATOYATEMPAN','CUAUTINCHAN','MIXTLA',
         'SANTO TOMAS HUEYOTLIPAN','TECALI DE HERRERA','TEPATLAXCO DE HIDALGO',
         'TLANEPANTLA','TZICATLACOYAN'],
    13: ['ACATZINGO','CUAPIAXTLA DE MADERO','MAZAPILTEPEC DE JUAREZ',
         'NOPALUCAN','RAFAEL LARA GRAJALES','LOS REYES DE JUAREZ',
         'SAN JOSE CHIAPA','SOLTEPEC','TEPEACA'],
    14: ['ALJOJUCA','ATZITZINTLA','CHALCHICOMULA DE SESMA','CHICHIQUILA',
         'CHILCHOTLA','ESPERANZA','ORIENTAL','QUIMIXTLAN',
         'SAN JUAN ATENCO','SAN NICOLAS BUENOS AIRES',
         'SAN SALVADOR EL SECO','TLACHICHUCA'],
    15: ['GENERAL FELIPE ANGELES','PALMAR DE BRAVO','QUECHOLAC',
         'SAN SALVADOR HUIXCOLOTLA','TECAMACHALCO','YEHUALTEPEC'],
    18: ['SAN ANDRES CHOLULA','SAN PEDRO CHOLULA'],
    21: ['ATLIXCO','ATZITZIHUACAN','OCOYUCAN',
         'SAN DIEGO LA MESA TOCHIMILTZINGO','SAN GREGORIO ATZOMPA',
         'SAN JERONIMO TECUANIPAN','SANTA ISABEL CHOLULA',
         'TIANGUISMANALCO','TOCHIMILCO'],
    22: ['ACTEOPAN','ALBINO ZERTUCHE','ATZALA','COHETZALA','COHUECAN',
         'CHIAUTLA','CHIETLA','CHILA DE LA SAL','HUAQUECHULA',
         'HUEHUETLAN EL CHICO','IXCAMILPA DE GUERRERO','IZUCAR DE MATAMOROS',
         'JOLALPAN','TEOTLALCO','TEPEMAXALCO','TEPEOJUMA','TEPEXCO',
         'TILAPA','TLAPANALA','XICOTLAN'],
    23: ['ACATLAN','AHUATLAN','AHUEHUETITLA','AXUTLA','COATZINGO',
         'CUAYUCA DE ANDRADE','CHIGMECATITLAN','CHILA','CHINANTLA','EPATLAN',
         'GUADALUPE','HUATLATLAUCA','HUEHUETLAN EL GRANDE','HUITZILTEPEC',
         'LA MAGDALENA TLATLAUQUITEPEC','MOLCAXAC','PETLALCINGO','PIAXTLA',
         'SAN JERONIMO XAYACATLAN','SAN JUAN ATZOMPA','SAN MARTIN TOTOLTEPEC',
         'SAN MIGUEL IXITLAN','SAN PABLO ANICANO','SAN PEDRO YELOIXTLAHUACA',
         'SANTA CATARINA TLALTEMPAN','SANTA INES AHUATEMPAN','TECOMATLAN',
         'TEHUITZINGO','TEOPANTLAN','TEPEXI DE RODRIGUEZ',
         'TEPEYAHUALCO DE CUAUHTEMOC','TOCHTEPEC','TOTOLTEPEC DE GUERRERO',
         'TULCINGO','XAYACATLAN DE BRAVO','XOCHILTEPEC',
         'XOCHITLAN TODOS SANTOS','ZACAPALA'],
    24: ['ATEXCAL','CALTEPEC','COYOTEPEC','IXCAQUIXTLA','JUAN N MENDEZ',
         'TEHUACAN','TEPANCO DE LOPEZ','TLACOTEPEC DE BENITO JUAREZ',
         'ZAPOTITLAN'],
    25: ['CANADA MORELOS','CHAPULCO','NICOLAS BRAVO','SANTIAGO MIAHUATLAN'],
    26: ['AJALPAN','ALTEPEXI','COXCATLAN','COYOMEAPAN','ELOXOCHITLAN',
         'SAN ANTONIO CANADA','SAN GABRIEL CHILAC','SAN JOSE MIAHUATLAN',
         'SAN SEBASTIAN TLACOTEPEC','VICENTE GUERRERO','ZINACATEPEC',
         'ZOQUITLAN'],
}

def _norm(s):
    s = s.upper()
    s = ''.join(c for c in unicodedata.normalize('NFD', s)
                if unicodedata.category(c) != 'Mn')
    s = ''.join(c if c.isalnum() or c == ' ' else ' ' for c in s)
    return ' '.join(s.split())

# Lookup inverso: nombre_normalizado → número de distrito
NOMBRE_A_DISTRITO = {}
for _num, _nombres in MUNS_POR_DISTRITO.items():
    for _n in _nombres:
        NOMBRE_A_DISTRITO[_norm(_n)] = _num

# ── 217 Municipios de Puebla (clave INEGI → nombre) ──────────────────────────
MUNICIPIOS = [
    ("001","Acajete"),("002","Acateno"),("003","Acatlán"),("004","Acatzingo"),
    ("005","Acteopan"),("006","Ahuacatlán"),("007","Ahuatlán"),("008","Ahuazotepec"),
    ("009","Ahuehuetitla"),("010","Ajalpan"),("011","Albino Zertuche"),("012","Aljojuca"),
    ("013","Altepexi"),("014","Amixtlán"),("015","Amozoc"),("016","Aquixtla"),
    ("017","Atempan"),("018","Atexcal"),("019","Atlixco"),("020","Atoyatempan"),
    ("021","Atzala"),("022","Atzitzihuacán"),("023","Atzitzintla"),("024","Axutla"),
    ("025","Ayotoxco de Guerrero"),("026","Calpan"),("027","Caltepec"),("028","Camocuautla"),
    ("029","Caxhuacan"),("030","Coatepec"),("031","Coatzingo"),("032","Cohetzala"),
    ("033","Cohuecan"),("034","Coronango"),("035","Coxcatlán"),("036","Coyomeapan"),
    ("037","Coyotepec"),("038","Cuapiaxtla de Madero"),("039","Cuautempan"),("040","Cuautinchán"),
    ("041","Cuautlancingo"),("042","Cuayuca de Andrade"),("043","Cuetzalan del Progreso"),("044","Cuyoaco"),
    ("045","Chalchicomula de Sesma"),("046","Chapulco"),("047","Chiautla"),("048","Chiautzingo"),
    ("049","Chiconcuautla"),("050","Chichiquila"),("051","Chietla"),("052","Chigmecatitlán"),
    ("053","Chignahuapan"),("054","Chignautla"),("055","Chila"),("056","Chila de la Sal"),
    ("057","Honey"),("058","Chilchotla"),("059","Chinantla"),("060","Domingo Arenas"),
    ("061","Eloxochitlán"),("062","Epatlán"),("063","Esperanza"),("064","Francisco Z. Mena"),
    ("065","General Felipe Ángeles"),("066","Guadalupe"),("067","Guadalupe Victoria"),("068","Hermenegildo Galeana"),
    ("069","Huaquechula"),("070","Huatlatlauca"),("071","Huauchinango"),("072","Huehuetla"),
    ("073","Huehuetlán el Chico"),("074","Huejotzingo"),("075","Hueyapan"),("076","Hueytamalco"),
    ("077","Hueytlalpan"),("078","Huitzilan de Serdán"),("079","Huitziltepec"),("080","Ignacio Allende"),
    ("081","Ixcamilpa de Guerrero"),("082","Ixcaquixtla"),("083","Ixtacamaxtitlán"),("084","Ixtepec"),
    ("085","Izúcar de Matamoros"),("086","Jalpan"),("087","Jolalpan"),("088","Jonotla"),
    ("089","Jopala"),("090","Juan C. Bonilla"),("091","Juan Galindo"),("092","Juan N. Méndez"),
    ("093","Lafragua"),("094","Libres"),("095","La Magdalena Tlatlauquitepec"),("096","Mazapiltepec de Juárez"),
    ("097","Mixtla"),("098","Molcaxac"),("099","Cañada Morelos"),("100","Naupan"),
    ("101","Nauzontla"),("102","Nealtican"),("103","Nicolás Bravo"),("104","Nopalucan"),
    ("105","Ocotepec"),("106","Ocoyucan"),("107","Olintla"),("108","Oriental"),
    ("109","Pahuatlán"),("110","Palmar de Bravo"),("111","Pantepec"),("112","Petlalcingo"),
    ("113","Piaxtla"),("114","Puebla"),("115","Quecholac"),("116","Quimixtlán"),
    ("117","Rafael Lara Grajales"),("118","Los Reyes de Juárez"),("119","San Andrés Cholula"),("120","San Antonio Cañada"),
    ("121","San Diego la Mesa Tochimiltzingo"),("122","San Felipe Teotlalcingo"),("123","San Felipe Tepatlán"),("124","San Gabriel Chilac"),
    ("125","San Gregorio Atzompa"),("126","San Jerónimo Tecuanipan"),("127","San Jerónimo Xayacatlán"),("128","San José Chiapa"),
    ("129","San José Miahuatlán"),("130","San Juan Atenco"),("131","San Juan Atzompa"),("132","San Martín Texmelucan"),
    ("133","San Martín Totoltepec"),("134","San Matías Tlalancaleca"),("135","San Miguel Ixitlán"),("136","San Miguel Xoxtla"),
    ("137","San Nicolás Buenos Aires"),("138","San Nicolás de los Ranchos"),("139","San Pablo Anicano"),("140","San Pedro Cholula"),
    ("141","San Pedro Yeloixtlahuaca"),("142","San Salvador el Seco"),("143","San Salvador el Verde"),("144","San Salvador Huixcolotla"),
    ("145","San Sebastián Tlacotepec"),("146","Santa Catarina Tlaltempan"),("147","Santa Inés Ahuatempan"),("148","Santa Isabel Cholula"),
    ("149","Santiago Miahuatlán"),("150","Santo Tomás Hueyotlipan"),("151","Soltepec"),("152","Tecali de Herrera"),
    ("153","Tecamachalco"),("154","Tecomatlán"),("155","Tehuacán"),("156","Tehuitzingo"),
    ("157","Tenampulco"),("158","Teopantlán"),("159","Tepanco de López"),("160","Tepango de Rodríguez"),
    ("161","Tepatlaxco de Hidalgo"),("162","Tepeaca"),("163","Tepemaxalco"),("164","Tepeojuma"),
    ("165","Tepetzintla"),("166","Tepexco"),("167","Tepexi de Rodríguez"),("168","Tepeyahualco"),
    ("169","Tepeyahualco de Cuauhtémoc"),("170","Tetela de Ocampo"),("171","Teteles de Ávila Castillo"),("172","Teziutlán"),
    ("173","Tianguismanalco"),("174","Tilapa"),("175","Tlacotepec de Benito Juárez"),("176","Tlacuilotepec"),
    ("177","Tlachichuca"),("178","Tlahuapan"),("179","Tlaltenango"),("180","Tlanepantla"),
    ("181","Tlaola"),("182","Tlapacoya"),("183","Tlapanalá"),("184","Tlatlauquitepec"),
    ("185","Tlaxco"),("186","Tochimilco"),("187","Tochtepec"),("188","Totoltepec de Guerrero"),
    ("189","Tulcingo"),("190","Tuzamapan de Galeana"),("191","Tzicatlacoyan"),("192","Venustiano Carranza"),
    ("193","Vicente Guerrero"),("194","Xayacatlán de Bravo"),("195","Xicotepec"),("196","Xicotlán"),
    ("197","Xiutetelco"),("198","Xochiapulco"),("199","Xochiltepec"),("200","Xochitlán de Vicente Suárez"),
    ("201","Xochitlán Todos Santos"),("202","Yahualica"),("203","Zacapala"),("204","Zacapoaxtla"),
    ("205","Zacatlán"),("206","Zapotitlán"),("207","Zapotitlán de Méndez"),("208","Zaragoza"),
    ("209","Zautla"),("210","Zihuateutla"),("211","Zinacatepec"),("212","Zongozotla"),
    ("213","Zoquiapan"),("214","Zoquitlán"),("215","Yehualtepec"),
    ("216","Huehuetlán el Grande"),("217","Teotlalco"),
]

# Fallbacks manuales para municipios difíciles de normalizar
FALLBACKS = {
    _norm("Ignacio Allende"):       8,   # municipio pequeño, área Huejotzingo
    _norm("Yahualica"):             4,   # Sierra Norte, área Zacapoaxtla
    _norm("Teotlalco"):            22,   # Mixteca, área Izúcar (en INE aparece en D22)
    _norm("Huehuetlán el Grande"): 23,   # Mixteca, área Acatlán
    _norm("Yehualtepec"):          15,   # Tecamachalco
}

INEGI_URL = (
    "https://geowebservices.inegi.org.mx/geoserver/MGN/ows"
    "?service=WFS&version=1.0.0&request=GetFeature"
    "&typeName=MGN:muni_2018_A&CQL_FILTER=CVE_ENT='21'"
    "&outputFormat=application/json"
)
GADM_URL = "https://geodata.ucdavis.edu/gadm/gadm4.1/json/gadm41_MEX_2.json"
GEOJSON_LOCAL = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    'data', 'puebla_municipios.geojson'
)


def _gadm_to_puebla(raw):
    features = []
    for f in raw.get('features', []):
        p = f['properties']
        if p.get('NAME_1') != 'Puebla':
            continue
        try:
            num = int(p['GID_2'].split('.')[2].split('_')[0])
            cve = str(num).zfill(3)
        except (KeyError, IndexError, ValueError):
            continue
        p['CVE_MUN'] = cve
        p['NOM_MUN'] = p.get('NAME_2', f'Municipio {cve}')
        features.append(f)
    return {'type': 'FeatureCollection', 'features': features}


class Command(BaseCommand):
    help = 'Carga la distritación electoral oficial INE 2017 para Puebla'

    def add_arguments(self, parser):
        parser.add_argument('--reset', action='store_true',
                            help='Borra datos existentes antes de cargar')
        parser.add_argument('--skip-geojson', action='store_true',
                            help='No descarga el GeoJSON')

    def handle(self, *args, **options):
        if options['reset']:
            self.stdout.write('⚠  Borrando datos existentes...')
            Municipio.objects.all().delete()
            Distrito.objects.all().delete()
            Division.objects.all().delete()

        # 1. Divisiones
        self.stdout.write('▶ Divisiones...')
        div_objs = {}
        for nombre, (color, nums) in DIVISIONES.items():
            div, _ = Division.objects.update_or_create(
                nombre=nombre, defaults={'color': color})
            div_objs[nombre] = div

        # 2. Distritos
        self.stdout.write('▶ Distritos...')
        dist_objs = {}
        for div_nombre, (_, nums) in DIVISIONES.items():
            for num in nums:
                dist, _ = Distrito.objects.update_or_create(
                    numero=num,
                    defaults={'nombre': CABECERAS[num], 'division': div_objs[div_nombre]})
                dist_objs[num] = dist
        self.stdout.write(f'   {len(dist_objs)} distritos OK')

        # 3. Municipios
        self.stdout.write('▶ Asignando municipios (fuente: INE 2017)...')
        asignados, sin_match = 0, []

        for cve, nombre in MUNICIPIOS:
            key = _norm(nombre)
            dist_num = NOMBRE_A_DISTRITO.get(key) or FALLBACKS.get(key)

            # Intento extra: quitar artículo inicial
            if dist_num is None:
                for pfx in ('LA ', 'LOS ', 'EL ', 'LAS '):
                    if key.startswith(pfx):
                        dist_num = NOMBRE_A_DISTRITO.get(key[len(pfx):])
                        if dist_num:
                            break

            if dist_num and dist_num in dist_objs:
                Municipio.objects.update_or_create(
                    cve_mun=cve,
                    defaults={'nombre': nombre, 'distrito': dist_objs[dist_num]})
                asignados += 1
            else:
                sin_match.append((cve, nombre))
                Municipio.objects.update_or_create(
                    cve_mun=cve, defaults={'nombre': nombre, 'distrito': None})

        self.stdout.write(f'   ✔ {asignados} asignados')
        if sin_match:
            self.stdout.write(self.style.WARNING(
                f'   ⚠ {len(sin_match)} sin match → ajustar en /admin:'))
            for cve, n in sin_match:
                self.stdout.write(f'      {cve} {n}')

        # 4. GeoJSON
        if not options['skip_geojson']:
            self._download_geojson()

        cache.delete('puebla_geojson_enriquecido')
        self.stdout.write(self.style.SUCCESS('\n✓ Listo → python manage.py runserver'))

    def _download_geojson(self):
        if os.path.exists(GEOJSON_LOCAL):
            self.stdout.write('▶ GeoJSON local ya existe, omitiendo descarga.')
            return
        import requests
        os.makedirs(os.path.dirname(GEOJSON_LOCAL), exist_ok=True)
        self.stdout.write('▶ Intentando INEGI WFS...')
        try:
            r = requests.get(INEGI_URL, timeout=30)
            r.raise_for_status()
            data = r.json()
            if len(data.get('features', [])) > 0:
                with open(GEOJSON_LOCAL, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False)
                self.stdout.write(self.style.SUCCESS(
                    f'   ✔ INEGI OK — {len(data["features"])} features'))
                return
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'   ✗ INEGI: {e}'))
        self.stdout.write('▶ Descargando GADM (México completo ~40 MB)...')
        try:
            import requests as req
            r = req.get(GADM_URL, timeout=180, stream=True)
            r.raise_for_status()
            chunks, total = [], 0
            for chunk in r.iter_content(chunk_size=1024*256):
                chunks.append(chunk)
                total += len(chunk)
                self.stdout.write(f'   {total/1_048_576:.0f} MB...', ending='\r')
                self.stdout.flush()
            data = _gadm_to_puebla(json.loads(b''.join(chunks)))
            with open(GEOJSON_LOCAL, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False)
            self.stdout.write(self.style.SUCCESS(
                f'\n   ✔ GADM OK — {len(data["features"])} municipios'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(
                f'\n   ✗ Descarga fallida: {e}\n'
                f'   Guarda el GeoJSON manualmente en:\n   {GEOJSON_LOCAL}'))
