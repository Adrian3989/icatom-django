from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from .models import Usuario, Sector, Enfermedad, Diagnostico
from .gemini_service import diagnosticar_planta
from django.http import HttpResponse
from .pdf_service import generar_pdf_historial
from django.db.models import Count, Avg
from .excel_service import generar_excel_historial
import json
import os


# ─── AUTENTICACIÓN ───────────────────────────────────────────

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        user = authenticate(request, email=email, password=password)
        if user and user.activo:
            login(request, user)
            return redirect('dashboard')
        messages.error(request, 'Correo o contraseña incorrectos.')
    return render(request, 'login.html')


def logout_view(request):
    logout(request)
    return redirect('login')


# ─── DASHBOARD ───────────────────────────────────────────────

@login_required
def dashboard_view(request):
    from django.db.models import Count
    import json
    
    if request.user.rol == 'trabajador':
        total = Diagnostico.objects.filter(usuario=request.user).count()
        recientes = Diagnostico.objects.filter(usuario=request.user)[:5]
        # Gráficas SOLO con sus datos
        enfermedades = Diagnostico.objects.filter(usuario=request.user).values('enfermedad__nombre').annotate(total=Count('id')).order_by('-total')[:5]
        severidad = Diagnostico.objects.filter(usuario=request.user).values('severidad').annotate(total=Count('id'))
    else:
        total = Diagnostico.objects.count()
        recientes = Diagnostico.objects.all()[:5]
        # Gráficas con TODOS los datos
        enfermedades = Diagnostico.objects.values('enfermedad__nombre').annotate(total=Count('id')).order_by('-total')[:5]
        severidad = Diagnostico.objects.values('severidad').annotate(total=Count('id'))
    
    enfermedades_chart = {
        'labels': [e['enfermedad__nombre'] or '—' for e in enfermedades],
        'values': [e['total'] for e in enfermedades]
    }

    diagnosticos_para_contar = diagnosticos_para_contar = Diagnostico.objects.filter(usuario=request.user) if request.user.rol == 'trabajador' else Diagnostico.objects.all()

    severidad_chart = {
    'labels': ['Leve', 'Moderado', 'Grave'],
    'values': [
        diagnosticos_para_contar.filter(severidad='leve').count(),
        diagnosticos_para_contar.filter(severidad='moderado').count(),
        diagnosticos_para_contar.filter(severidad='grave').count(),
        ]
    }

    return render(request, 'dashboard.html', {
        'total': total,
        'recientes': recientes,
        'enfermedades_chart': json.dumps(enfermedades_chart),
        'severidad_chart': json.dumps(severidad_chart),
    })


# ─── DIAGNÓSTICO ─────────────────────────────────────────────

@login_required
def nuevo_diagnostico(request):
    sectores = Sector.objects.filter(activo=True)
    if request.method == 'POST':
        imagen = request.FILES.get('imagen')
        sector_id = request.POST.get('sector')

        if not imagen or not sector_id:
            messages.error(request, 'Debes subir una imagen y seleccionar un sector.')
            return render(request, 'nuevo_diagnostico.html', {'sectores': sectores})

        # Guardar diagnóstico temporal
        sector = get_object_or_404(Sector, id=sector_id)
        diag = Diagnostico.objects.create(
            usuario=request.user,
            sector=sector,
            imagen=imagen,
        )

        # Llamar a Gemini
        resultado = diagnosticar_planta(diag.imagen.path)

        if resultado.get('error'):
            diag.delete()
            messages.error(request, resultado['mensaje'])
            return render(request, 'nuevo_diagnostico.html', {'sectores': sectores})

        if not resultado.get('es_valida'):
            diag.delete()
            messages.error(request, resultado.get('mensaje', 'Imagen no válida.'))
            return render(request, 'nuevo_diagnostico.html', {'sectores': sectores})

        # Guardar resultado
        enfermedad, _ = Enfermedad.objects.get_or_create(
            nombre=resultado.get('enfermedad', 'No determinada')
        )
        diag.enfermedad = enfermedad
        diag.severidad = resultado.get('severidad', 'leve')
        diag.sintomas = resultado.get('sintomas', '')
        diag.tratamiento = resultado.get('tratamiento', '')
        diag.respuesta_ia = str(resultado)
        diag.confianza_ia = resultado.get('confianza', 0.0)
        diag.es_valida = True

        # Advertencia si confianza es baja
        if diag.confianza_ia < 0.5:
            messages.warning(request, '⚠️ Confianza baja. Se recomienda consultar con el ingeniero agrónomo.')

        diag.save()
        return redirect('detalle_diagnostico', pk=diag.id)

    return render(request, 'nuevo_diagnostico.html', {'sectores': sectores})


@login_required
def detalle_diagnostico(request, pk):
    diag = get_object_or_404(Diagnostico, id=pk)
    if request.user.rol == 'trabajador' and diag.usuario != request.user:
        messages.error(request, 'No tienes permiso para ver este diagnóstico.')
        return redirect('historial')
    return render(request, 'detalle_diagnostico.html', {'diag': diag})


# ─── HISTORIAL ───────────────────────────────────────────────

@login_required
def historial_view(request):
    from datetime import datetime
    
    if request.user.rol == 'trabajador':
        diagnosticos = Diagnostico.objects.filter(usuario=request.user)
    else:
        diagnosticos = Diagnostico.objects.all()

    # Filtros
    enfermedad_filtro = request.GET.get('enfermedad')
    sector_filtro = request.GET.get('sector')
    fecha_desde = request.GET.get('fecha_desde')
    fecha_hasta = request.GET.get('fecha_hasta')
    
    if enfermedad_filtro:
        diagnosticos = diagnosticos.filter(enfermedad__nombre__icontains=enfermedad_filtro)
    if sector_filtro:
        diagnosticos = diagnosticos.filter(sector__id=sector_filtro)
    if fecha_desde:
        diagnosticos = diagnosticos.filter(fecha_consulta__date__gte=fecha_desde)
    if fecha_hasta:
        diagnosticos = diagnosticos.filter(fecha_consulta__date__lte=fecha_hasta)

    sectores = Sector.objects.filter(activo=True)
    return render(request, 'historial.html', {
        'diagnosticos': diagnosticos,
        'sectores': sectores,
    })


# ─── REPORTES ────────────────────────────────────────────────

@login_required
def reportes_view(request):
    if request.user.rol == 'trabajador':
        return redirect('dashboard')

    # Datos para gráficas
    enfermedades = Diagnostico.objects.values('enfermedad__nombre').annotate(total=Count('id')).order_by('-total')[:10]
    sectores = Diagnostico.objects.values('sector__nombre').annotate(total=Count('id')).order_by('-total')
    usuarios = Diagnostico.objects.values('usuario__nombre').annotate(total=Count('id')).order_by('-total')
    severidad = Diagnostico.objects.values('severidad').annotate(total=Count('id'))

    # Preparar datos para Chart.js
    enfermedades_chart = {
        'labels': [e['enfermedad__nombre'] or '—' for e in enfermedades],
        'values': [e['total'] for e in enfermedades]
    }
    sectores_chart = {
        'labels': [s['sector__nombre'] or '—' for s in sectores],
        'values': [s['total'] for s in sectores]
    }
    usuarios_chart = {
    'labels': [u['usuario__nombre'] or '—' for u in usuarios],
    'values': [u['total'] for u in usuarios]
    }
    severidad_chart = {
    'labels': ['Leve', 'Moderado', 'Grave'],
    'values': [
        Diagnostico.objects.filter(severidad='leve').count(),
        Diagnostico.objects.filter(severidad='moderado').count(),
        Diagnostico.objects.filter(severidad='grave').count(),
        ]   
    }

    # Estadísticas extra
    diagnosticos_total = Diagnostico.objects.count()
    diagnosticos_graves = Diagnostico.objects.filter(severidad='grave').count()
    usuarios_activos = Usuario.objects.filter(activo=True).count()
    confianza_promedio = Diagnostico.objects.aggregate(prom=Avg('confianza_ia'))['prom']
    confianza_promedio = int(confianza_promedio * 100) if confianza_promedio else 0

    import json
    return render(request, 'reportes.html', {
        'enfermedades_chart': json.dumps(enfermedades_chart),
        'sectores_chart': json.dumps(sectores_chart),
        'usuarios_chart': json.dumps(usuarios_chart),
        'severidad_chart': json.dumps(severidad_chart),
        'diagnosticos_total': diagnosticos_total,
        'diagnosticos_graves': diagnosticos_graves,
        'usuarios_activos': usuarios_activos,
        'confianza_promedio': confianza_promedio,
    })

# ─── GESTIÓN DE USUARIOS ─────────────────────────────────────

@login_required
def usuarios_view(request):
    if request.user.rol != 'administrador':
        return redirect('dashboard')
    usuarios = Usuario.objects.all()
    return render(request, 'usuarios.html', {'usuarios': usuarios})


@login_required
def crear_usuario(request):
    if request.user.rol != 'administrador':
        return redirect('dashboard')
    sectores = Sector.objects.filter(activo=True)
    if request.method == 'POST':
        try:
            Usuario.objects.create_user(
                email=request.POST['email'],
                nombre=request.POST['nombre'],
                password=request.POST['password'],
                rol=request.POST['rol'],
            )
            messages.success(request, 'Usuario creado correctamente.')
            return redirect('usuarios')
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
    return render(request, 'crear_usuario.html', {'sectores': sectores})


@login_required
def editar_usuario(request, pk):
    if request.user.rol != 'administrador':
        return redirect('dashboard')
    usuario = get_object_or_404(Usuario, id=pk)
    if request.method == 'POST':
        usuario.nombre = request.POST.get('nombre', usuario.nombre)
        usuario.rol = request.POST.get('rol', usuario.rol)
        usuario.activo = request.POST.get('activo') == 'on'
        usuario.save()
        messages.success(request, 'Usuario actualizado.')
        return redirect('usuarios')
    return render(request, 'editar_usuario.html', {'usuario': usuario})


# ─── API REST ─────────────────────────────────────────────────

class DiagnosticoAPIView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        imagen = request.FILES.get('imagen')
        sector_id = request.data.get('sector_id')
        if not imagen or not sector_id:
            return Response({'error': 'imagen y sector_id son requeridos'}, status=400)
        sector = get_object_or_404(Sector, id=sector_id)
        diag = Diagnostico.objects.create(
            usuario=request.user,
            sector=sector,
            imagen=imagen,
        )
        resultado = diagnosticar_planta(diag.imagen.path)
        if resultado.get('error') or not resultado.get('es_valida'):
            diag.delete()
            return Response(resultado, status=400)
        enfermedad, _ = Enfermedad.objects.get_or_create(
            nombre=resultado.get('enfermedad', 'No determinada')
        )
        diag.enfermedad = enfermedad
        diag.severidad = resultado.get('severidad', 'leve')
        diag.sintomas = resultado.get('sintomas', '')
        diag.tratamiento = resultado.get('tratamiento', '')
        diag.respuesta_ia = str(resultado)
        diag.confianza_ia = resultado.get('confianza', 0.0)
        diag.es_valida = True
        diag.save()
        return Response({'id': diag.id, 'enfermedad': diag.enfermedad.nombre,
                         'severidad': diag.severidad, 'tratamiento': diag.tratamiento})


class HistorialAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.rol == 'trabajador':
            diagnosticos = Diagnostico.objects.filter(usuario=request.user)
        else:
            diagnosticos = Diagnostico.objects.all()
        data = [{'id': d.id, 'enfermedad': d.enfermedad.nombre if d.enfermedad else '',
                 'severidad': d.severidad, 'fecha': d.fecha_consulta,
                 'sector': d.sector.nombre if d.sector else ''} for d in diagnosticos]
        return Response(data)


class ReportesAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.rol == 'trabajador':
            return Response({'error': 'Sin permiso'}, status=403)
        enfermedades = list(
            Diagnostico.objects.values('enfermedad__nombre')
            .annotate(total=Count('id'))
            .order_by('-total')[:10]
        )
        return Response({'enfermedades': enfermedades})

@login_required
def exportar_pdf(request):
    from datetime import datetime
    
    if request.user.rol == 'trabajador':
        diagnosticos = Diagnostico.objects.filter(usuario=request.user)
    else:
        diagnosticos = Diagnostico.objects.all()

    # Capturar filtros
    enfermedad_filtro = request.GET.get('enfermedad', '').strip()
    sector_filtro = request.GET.get('sector', '').strip()
    fecha_desde = request.GET.get('fecha_desde', '').strip()
    fecha_hasta = request.GET.get('fecha_hasta', '').strip()
    
    # Aplicar filtros
    if enfermedad_filtro:
        diagnosticos = diagnosticos.filter(enfermedad__nombre__icontains=enfermedad_filtro)
    if sector_filtro:
        diagnosticos = diagnosticos.filter(sector__id=sector_filtro)
    if fecha_desde:
        diagnosticos = diagnosticos.filter(fecha_consulta__date__gte=fecha_desde)
    if fecha_hasta:
        diagnosticos = diagnosticos.filter(fecha_consulta__date__lte=fecha_hasta)

    buffer = generar_pdf_historial(diagnosticos, request.user)

    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="historial_icatom.pdf"'
    return response

@login_required
def exportar_excel(request):
    if request.user.rol == 'trabajador':
        diagnosticos = Diagnostico.objects.filter(usuario=request.user)
    else:
        diagnosticos = Diagnostico.objects.all()

    # Aplicar filtros igual que en historial
    enfermedad_filtro = request.GET.get('enfermedad')
    sector_filtro = request.GET.get('sector')
    fecha_desde = request.GET.get('fecha_desde')
    fecha_hasta = request.GET.get('fecha_hasta')
    
    if enfermedad_filtro:
        diagnosticos = diagnosticos.filter(enfermedad__nombre__icontains=enfermedad_filtro)
    if sector_filtro:
        diagnosticos = diagnosticos.filter(sector__id=sector_filtro)
    if fecha_desde:
        diagnosticos = diagnosticos.filter(fecha_consulta__date__gte=fecha_desde)
    if fecha_hasta:
        diagnosticos = diagnosticos.filter(fecha_consulta__date__lte=fecha_hasta)

    buffer = generar_excel_historial(diagnosticos, request.user)

    response = HttpResponse(buffer, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="historial_icatom.xlsx"'
    return response
