from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator


class DatosPersonales(models.Model):
    idperfil = models.IntegerField(primary_key=True, validators=[MinValueValidator(1)])
    fotoperfil = models.ImageField(upload_to='perfil/', null=True, blank=True)
    email_contacto = models.EmailField(max_length=100, null=True, blank=True)
    descripcionperfil = models.CharField(max_length=300)
    perfilactivo = models.IntegerField(validators=[MinValueValidator(1)])
    apellidos = models.CharField(max_length=60)
    nombres = models.CharField(max_length=60)
    nacionalidad = models.CharField(max_length=20)
    lugarnacimiento = models.CharField(max_length=60)
    fechanacimiento = models.DateField()
    numerocedula = models.CharField(max_length=10, unique=True)
    sexo_choices = [('H', 'Hombre'), ('M', 'Mujer')]
    sexo = models.CharField(max_length=1, choices=sexo_choices)
    estadocivil = models.CharField(max_length=50) 
    licenciaconducir = models.CharField(max_length=20, blank=True, null=True)
    telefonoconvencional = models.CharField(max_length=10, blank=True, null=True)
    telefonofijo = models.CharField(max_length=10, blank=True, null=True)
    direcciontrabajo = models.CharField(max_length=100, blank=True, null=True)
    direcciondomiciliaria = models.CharField(max_length=100)
    sitioweb = models.CharField(max_length=200, blank=True, null=True)
    
    def clean(self):
        super().clean()
        if self.fechanacimiento and self.fechanacimiento > timezone.now().date():
            raise ValidationError({'fechanacimiento': "La fecha de nacimiento no puede ser futura."})
        
    def __str__(self):
        return f"{self.nombres} {self.apellidos}"

    class Meta:
        verbose_name_plural = "Datos Personales"


class ExperienciaLaboral(models.Model):
    idexperiencilaboral = models.IntegerField(primary_key=True, validators=[MinValueValidator(1)])
    idperfilconqueestaactivo = models.ForeignKey(DatosPersonales, on_delete=models.CASCADE)
    cargodesempenado = models.CharField(max_length=200)
    nombrempresa = models.CharField(max_length=150)
    lugarempresa = models.CharField(max_length=150)
    emailempresa = models.EmailField(max_length=200)
    sitiowebempresa = models.URLField(max_length=500, blank=True, null=True)
    nombrecontactoempresarial = models.CharField(max_length=200)
    telefonocontactoempresarial = models.CharField(max_length=100)
    fechainiciogestion = models.DateField()
    fechafingestion = models.DateField(blank=True, null=True)
    descripcionfunciones = models.TextField()
    activarparaqueseveaenfront = models.BooleanField(default=True)
    rutacertificado = models.FileField(upload_to='certificados/experiencia/', blank=True, null=True)

    def clean(self):
        super().clean()
        hoy = timezone.now().date()
        if self.fechainiciogestion and self.fechainiciogestion > hoy:
            raise ValidationError({'fechainiciogestion': "Inicio de gestión no puede ser futuro."})
        if self.fechafingestion and self.fechafingestion > hoy:
            raise ValidationError({'fechafingestion': "Fin de gestión no puede ser futuro."})
        if self.fechainiciogestion and self.fechafingestion and self.fechafingestion < self.fechainiciogestion:
            raise ValidationError({'fechafingestion': "El fin no puede ser antes del inicio."})

    def __str__(self):
        return f"{self.cargodesempenado} en {self.nombrempresa}"

    class Meta:
        ordering = ['-fechainiciogestion']

class Reconocimientos(models.Model):
    TIPO_CHOICES = [('Académico', 'Académico'), ('Público', 'Público'), ('Privado', 'Privado')]
    idreconocimiento = models.IntegerField(primary_key=True, validators=[MinValueValidator(1)])
    idperfilconqueestaactivo = models.ForeignKey(DatosPersonales, on_delete=models.CASCADE)
    tiporeconocimiento = models.CharField(max_length=200, choices=TIPO_CHOICES)
    fechareconocimiento = models.DateField()
    descripcionreconocimiento = models.TextField()
    entidadpatrocinadora = models.CharField(max_length=300)
    nombrecontactoauspicia = models.CharField(max_length=300)
    telefonocontactoauspicia = models.CharField(max_length=100)
    activarparaqueseveaenfront = models.BooleanField(default=True)
    rutacertificado = models.FileField(upload_to='reconocimientos/', null=True, blank=True)

    def clean(self):
        super().clean()
        if self.fechareconocimiento and self.fechareconocimiento > timezone.now().date():
            raise ValidationError({'fechareconocimiento': "La fecha no puede ser futura."})

    def __str__(self):
        return self.descripcionreconocimiento

class CursosRealizados(models.Model):
    idcursorealizado = models.IntegerField(primary_key=True, validators=[MinValueValidator(1)])
    idperfilconqueestaactivo = models.ForeignKey(DatosPersonales, on_delete=models.CASCADE)
    nombrecurso = models.CharField(max_length=250)
    fechainicio = models.DateField()
    fechafin = models.DateField()
    totalhoras = models.IntegerField(validators=[MinValueValidator(1)])
    descripcioncurso = models.TextField()
    entidadpatrocinadora = models.CharField(max_length=150)
    nombrecontactoauspicia = models.CharField(max_length=200)
    telefonocontactoauspicia = models.CharField(max_length=60)
    emailempresapatrocinadora = models.EmailField(max_length=150)
    activarparaqueseveaenfront = models.BooleanField(default=True)
    rutacertificado = models.FileField(upload_to='certificados/cursos/', blank=True, null=True)

    def clean(self):
        super().clean()
        hoy = timezone.now().date()
        if self.fechainicio and self.fechainicio > hoy:
            raise ValidationError({'fechainicio': "El inicio no puede ser futuro."})
        if self.fechafin and self.fechafin > hoy:
            raise ValidationError({'fechafin': "El fin no puede ser futuro."})
        if self.fechainicio and self.fechafin and self.fechafin < self.fechainicio:
            raise ValidationError({'fechafin': "El fin debe ser posterior al inicio."})

    def __str__(self):
        return self.nombrecurso

class ProductosAcademicos(models.Model):
    idproductoacademico = models.IntegerField(primary_key=True, validators=[MinValueValidator(1)])
    idperfilconqueestaactivo = models.ForeignKey(DatosPersonales, on_delete=models.CASCADE)
    nombrerecurso = models.CharField(max_length=200)
    clasificador = models.CharField(max_length=100)
    descripcion = models.TextField()
    # NUEVO CAMPO DE IMAGEN
    imagen_producto = models.ImageField(upload_to='academicos/', null=True, blank=True, verbose_name="Imagen Representativa")
    activarparaqueseveaenfront = models.BooleanField(default=True)

    def __str__(self):
        return self.nombrerecurso

class ProductosLaborales(models.Model):
    idproductoslaborales = models.IntegerField(primary_key=True, validators=[MinValueValidator(1)])
    idperfilconqueestaactivo = models.ForeignKey(DatosPersonales, on_delete=models.CASCADE)
    nombreproducto = models.CharField(max_length=100)
    fechaproducto = models.DateField()
    descripcion = models.TextField() 
    url_proyecto = models.URLField(max_length=500, blank=True, null=True)
    activarparaqueseveaenfront = models.BooleanField(default=True)

    def clean(self):
        super().clean()
        if self.fechaproducto and self.fechaproducto > timezone.now().date():
            raise ValidationError({'fechaproducto': "La fecha del producto no puede ser futura."})

    def __str__(self):
        return self.nombreproducto

class VentaGarage(models.Model):
    ESTADO_CHOICES = [('Bueno', 'Bueno'), ('Regular', 'Regular')]
    # ID mayor a 0
    idventagarage = models.IntegerField(primary_key=True, validators=[MinValueValidator(1)])
    idperfilconqueestaactivo = models.ForeignKey(DatosPersonales, on_delete=models.CASCADE)
    nombreproducto = models.CharField(max_length=100)
    estadoproducto = models.CharField(max_length=40, choices=ESTADO_CHOICES)
    foto_producto = models.ImageField(upload_to='garage/fotos/', null=True, blank=True, verbose_name="Foto para la Web")
    documento_interes = models.FileField(upload_to='garage/documentos/', null=True, blank=True, verbose_name="PDF solo para el CV")
    descripcion = models.TextField()
    valordelbien = models.DecimalField(max_digits=7, decimal_places=2, validators=[MinValueValidator(0)])
    activarparaqueseveaenfront = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.nombreproducto} - ${self.valordelbien}"