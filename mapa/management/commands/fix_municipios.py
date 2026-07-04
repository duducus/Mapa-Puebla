"""
fix_municipios.py — Corrección definitiva de municipios con nombres incorrectos.

Problemas corregidos:
  1. "Yahualica" (CVE 202) → no es municipio de Puebla; renombrar a "Yaonáhuac" → D5
  2. "Yehualtepec" (CVE 215) fue cambiado a "Atlequizayan" en una versión anterior
     del script → revertir CVE 215 a "Yehualtepec" → D15
  3. "Atlequizayan" no tenía registro en la BD → crear con CVE 218 → D4

Corre con: python manage.py fix_municipios
"""
from django.core.management.base import BaseCommand
from django.core.cache import cache
from mapa.models import Municipio, Distrito


class Command(BaseCommand):
    help = 'Corrige Yaonáhuac (D5), Yehualtepec (D15) y Atlequizayan (D4)'

    def handle(self, *args, **options):
        errores = False

        def get_dist(num):
            try:
                return Distrito.objects.get(numero=num)
            except Distrito.DoesNotExist:
                self.stdout.write(self.style.ERROR(
                    f'No existe Distrito {num}. Corre primero: python manage.py seed_data'))
                return None

        d4  = get_dist(4)
        d5  = get_dist(5)
        d15 = get_dist(15)
        if not all([d4, d5, d15]):
            return

        # ── 1. Yaonáhuac (D5) ────────────────────────────────────────────────
        # CVE 202 tenía "Yahualica" (municipio de Jalisco, no existe en Puebla)
        try:
            m = Municipio.objects.get(cve_mun='202')
            if m.nombre != 'Yaonáhuac':
                self.stdout.write(
                    f'  CVE 202: "{m.nombre}" → "Yaonáhuac" (D5)')
                m.nombre   = 'Yaonáhuac'
                m.distrito = d5
                m.save()
                self.stdout.write(self.style.SUCCESS('  ✔ Yaonáhuac corregido'))
            else:
                # Ya tiene el nombre correcto; solo asegurar distrito correcto
                if m.distrito != d5:
                    m.distrito = d5
                    m.save()
                    self.stdout.write(self.style.SUCCESS('  ✔ Yaonáhuac → D5 (distrito corregido)'))
                else:
                    self.stdout.write('  · Yaonáhuac ya está correcto')
        except Municipio.DoesNotExist:
            self.stdout.write(self.style.WARNING('  ⚠ No se encontró CVE 202'))

        # ── 2. Yehualtepec (D15) ─────────────────────────────────────────────
        # CVE 215 puede tener "Atlequizayan" si se corrió una versión anterior
        # del script; restaurarlo a "Yehualtepec"
        try:
            m = Municipio.objects.get(cve_mun='215')
            if m.nombre != 'Yehualtepec':
                self.stdout.write(
                    f'  CVE 215: "{m.nombre}" → "Yehualtepec" (D15)')
                m.nombre   = 'Yehualtepec'
                m.distrito = d15
                m.save()
                self.stdout.write(self.style.SUCCESS('  ✔ Yehualtepec restaurado'))
            else:
                if m.distrito != d15:
                    m.distrito = d15
                    m.save()
                    self.stdout.write(self.style.SUCCESS('  ✔ Yehualtepec → D15'))
                else:
                    self.stdout.write('  · Yehualtepec ya está correcto')
        except Municipio.DoesNotExist:
            Municipio.objects.create(cve_mun='215', nombre='Yehualtepec', distrito=d15)
            self.stdout.write(self.style.SUCCESS('  ✔ Yehualtepec creado (CVE 215, D15)'))

        # ── 3. Atlequizayan (D4) ─────────────────────────────────────────────
        # No existía en la lista original de 217; se crea con CVE 218
        if Municipio.objects.filter(nombre='Atlequizayan').exists():
            m = Municipio.objects.get(nombre='Atlequizayan')
            if m.distrito != d4:
                m.distrito = d4
                m.save()
                self.stdout.write(self.style.SUCCESS('  ✔ Atlequizayan → D4'))
            else:
                self.stdout.write('  · Atlequizayan ya está correcto')
        else:
            Municipio.objects.update_or_create(
                cve_mun='218',
                defaults={'nombre': 'Atlequizayan', 'distrito': d4}
            )
            self.stdout.write(self.style.SUCCESS('  ✔ Atlequizayan creado (CVE 218, D4)'))

        # ── Limpiar caché ─────────────────────────────────────────────────────
        for k in ['puebla_geojson_v5', 'puebla_geojson_v6']:
            cache.delete(k)

        self.stdout.write(self.style.SUCCESS(
            '\n✓ Listo. Reinicia el servidor para ver los cambios.'))
