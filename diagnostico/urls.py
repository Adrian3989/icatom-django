from django.urls import path
from . import views

urlpatterns = [
    # Autenticación
    path('', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Dashboard
    path('dashboard/', views.dashboard_view, name='dashboard'),

    # Diagnóstico
    path('diagnostico/nuevo/', views.nuevo_diagnostico, name='nuevo_diagnostico'),
    path('diagnostico/<int:pk>/', views.detalle_diagnostico, name='detalle_diagnostico'),

    # Historial
    path('historial/', views.historial_view, name='historial'),

    # Reportes
    path('reportes/', views.reportes_view, name='reportes'),

    # Gestión de usuarios (solo admin)
    path('usuarios/', views.usuarios_view, name='usuarios'),
    path('usuarios/crear/', views.crear_usuario, name='crear_usuario'),
    path('usuarios/<int:pk>/editar/', views.editar_usuario, name='editar_usuario'),

    # API REST
    path('api/diagnostico/', views.DiagnosticoAPIView.as_view(), name='api_diagnostico'),
    path('api/historial/', views.HistorialAPIView.as_view(), name='api_historial'),
    path('api/reportes/', views.ReportesAPIView.as_view(), name='api_reportes'),

    #Exportar PDF
    path('historial/exportar/', views.exportar_pdf, name='exportar_pdf'),

    #Exportar Excel
    path('historial/exportar-excel/', views.exportar_excel, name='exportar_excel'),
]