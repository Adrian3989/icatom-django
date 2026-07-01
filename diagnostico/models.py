from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin

class UsuarioManager(BaseUserManager):
    def create_user(self, email, nombre, password=None, **extra_fields):
        if not email:
            raise ValueError('El email es obligatorio')
        email = self.normalize_email(email)
        user = self.model(email=email, nombre=nombre, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, nombre, password=None, **extra_fields):
        extra_fields.setdefault('rol', 'administrador')
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, nombre, password, **extra_fields)


class Usuario(AbstractBaseUser, PermissionsMixin):
    ROL_CHOICES = [
        ('trabajador', 'Trabajador de Campo'),
        ('agronomo', 'Agrónomo'),
        ('administrador', 'Administrador'),
    ]
    nombre = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    rol = models.CharField(max_length=20, choices=ROL_CHOICES, default='trabajador')
    activo = models.BooleanField(default=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)
    is_staff = models.BooleanField(default=False)

    objects = UsuarioManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['nombre']

    def __str__(self):
        return f'{self.nombre} ({self.rol})'


class Sector(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre


class Enfermedad(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre


class Diagnostico(models.Model):
    SEVERIDAD_CHOICES = [
        ('leve', 'Leve'),
        ('moderado', 'Moderado'),
        ('grave', 'Grave'),
    ]
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='diagnosticos')
    sector = models.ForeignKey(Sector, on_delete=models.SET_NULL, null=True)
    enfermedad = models.ForeignKey(Enfermedad, on_delete=models.SET_NULL, null=True, blank=True)
    imagen = models.ImageField(upload_to='diagnosticos/')
    severidad = models.CharField(max_length=20, choices=SEVERIDAD_CHOICES, blank=True)
    sintomas = models.TextField(blank=True)
    tratamiento = models.TextField(blank=True)
    respuesta_ia = models.TextField(blank=True)
    confianza_ia = models.FloatField(default=0.0)
    fecha_consulta = models.DateTimeField(auto_now_add=True)
    es_valida = models.BooleanField(default=True)

    class Meta:
        ordering = ['-fecha_consulta']

    def __str__(self):
        return f'Diagnóstico #{self.id} - {self.usuario.nombre}'