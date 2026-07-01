from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario, Sector, Enfermedad, Diagnostico

@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    list_display = ['nombre', 'email', 'rol', 'activo']
    list_filter = ['rol', 'activo']
    search_fields = ['nombre', 'email']
    ordering = ['nombre']
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Información personal', {'fields': ('nombre', 'rol', 'activo')}),
        ('Permisos', {'fields': ('is_staff', 'is_superuser')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'nombre', 'password1', 'password2', 'rol'),
        }),
    )

@admin.register(Sector)
class SectorAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'descripcion', 'activo']

@admin.register(Enfermedad)
class EnfermedadAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'descripcion', 'activo']

@admin.register(Diagnostico)
class DiagnosticoAdmin(admin.ModelAdmin):
    list_display = ['id', 'usuario', 'enfermedad', 'severidad', 'sector', 'fecha_consulta']
    list_filter = ['severidad', 'sector']