from django.db import models


class Division(models.Model):
    nombre = models.CharField(max_length=100)
    color  = models.CharField(max_length=7, default='#3388ff', help_text='Color hex, ej: #E74C3C')

    class Meta:
        verbose_name = 'División'
        verbose_name_plural = 'Divisiones'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class Distrito(models.Model):
    numero   = models.IntegerField(unique=True, verbose_name='Número')
    nombre   = models.CharField(max_length=100)
    division = models.ForeignKey(
        Division, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='distritos', verbose_name='División'
    )

    class Meta:
        verbose_name = 'Distrito'
        verbose_name_plural = 'Distritos'
        ordering = ['numero']

    def __str__(self):
        return f'Distrito {self.numero} – {self.nombre}'


class Municipio(models.Model):
    cve_mun  = models.CharField(max_length=3, unique=True, verbose_name='Clave INEGI')
    nombre   = models.CharField(max_length=200)
    distrito = models.ForeignKey(
        Distrito, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='municipios'
    )

    class Meta:
        verbose_name = 'Municipio'
        verbose_name_plural = 'Municipios'
        ordering = ['cve_mun']

    def __str__(self):
        return f'{self.cve_mun} – {self.nombre}'
