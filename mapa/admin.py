from django.contrib import admin
from .models import Division, Distrito, Municipio


@admin.register(Division)
class DivisionAdmin(admin.ModelAdmin):
    list_display  = ('nombre', 'color', 'num_distritos')
    search_fields = ('nombre',)

    def num_distritos(self, obj):
        return obj.distritos.count()
    num_distritos.short_description = 'Distritos'


class MunicipioInline(admin.TabularInline):
    model  = Municipio
    extra  = 0
    fields = ('cve_mun', 'nombre')


@admin.register(Distrito)
class DistritoAdmin(admin.ModelAdmin):
    list_display   = ('numero', 'nombre', 'division', 'num_municipios')
    list_filter    = ('division',)
    search_fields  = ('nombre',)
    inlines        = [MunicipioInline]

    def num_municipios(self, obj):
        return obj.municipios.count()
    num_municipios.short_description = 'Municipios'


@admin.register(Municipio)
class MunicipioAdmin(admin.ModelAdmin):
    list_display  = ('cve_mun', 'nombre', 'distrito', 'division')
    list_filter   = ('distrito__division', 'distrito')
    search_fields = ('nombre', 'cve_mun')

    def division(self, obj):
        return obj.distrito.division if obj.distrito else '—'
    division.short_description = 'División'
