from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.enums import TA_CENTER, TA_LEFT
import io

def generar_pdf_historial(diagnosticos, usuario):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )

    styles = getSampleStyleSheet()
    elementos = []

    # ESTILO TÍTULO
    estilo_titulo = ParagraphStyle(
        'titulo',
        parent=styles['Title'],
        fontSize=20,
        textColor=colors.HexColor('#1b5e20'),
        spaceAfter=4,
        alignment=TA_CENTER
    )
    estilo_subtitulo = ParagraphStyle(
        'subtitulo',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#555555'),
        spaceAfter=2,
        alignment=TA_CENTER
    )
    estilo_seccion = ParagraphStyle(
        'seccion',
        parent=styles['Normal'],
        fontSize=11,
        textColor=colors.HexColor('#1b5e20'),
        fontName='Helvetica-Bold',
        spaceAfter=6,
        spaceBefore=10
    )
    estilo_normal = ParagraphStyle(
        'normal',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.HexColor('#333333'),
        spaceAfter=2
    )

    # ENCABEZADO
    elementos.append(Paragraph('🍅 ICATOM S.A.', estilo_titulo))
    elementos.append(Paragraph('Sistema de Diagnóstico Fitosanitario', estilo_subtitulo))
    elementos.append(Paragraph('Ica, Perú', estilo_subtitulo))
    elementos.append(Spacer(1, 0.3*cm))
    elementos.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor('#1b5e20')))
    elementos.append(Spacer(1, 0.3*cm))

    # DATOS DEL REPORTE
    elementos.append(Paragraph('REPORTE DE HISTORIAL DE DIAGNÓSTICOS', estilo_seccion))
    elementos.append(Paragraph(f'Usuario: {usuario.nombre}', estilo_normal))
    elementos.append(Paragraph(f'Rol: {usuario.get_rol_display()}', estilo_normal))
    elementos.append(Paragraph(f'Total de diagnósticos: {diagnosticos.count()}', estilo_normal))
    elementos.append(Spacer(1, 0.4*cm))

    # TABLA
    if diagnosticos.exists():
        datos_tabla = [['#', 'Fecha', 'Enfermedad', 'Severidad', 'Sector', 'Confianza']]

        for d in diagnosticos:
            datos_tabla.append([
                str(d.id),
                d.fecha_consulta.strftime('%d/%m/%Y %H:%M'),
                d.enfermedad.nombre if d.enfermedad else '—',
                d.severidad.capitalize() if d.severidad else '—',
                d.sector.nombre if d.sector else '—',
                f"{d.confianza_ia:.0%}" if d.confianza_ia else '—',
            ])

        tabla = Table(datos_tabla, colWidths=[
            1.2*cm, 3.5*cm, 4.5*cm, 2.5*cm, 3*cm, 2.3*cm
        ])
        tabla.setStyle(TableStyle([
            # Encabezado
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1b5e20')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('TOPPADDING', (0, 0), (-1, 0), 8),
            # Filas
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('ALIGN', (0, 1), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 1), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
            # Colores alternos
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f1f8e9')]),
            # Bordes
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#1b5e20')),
        ]))
        elementos.append(tabla)
    else:
        elementos.append(Paragraph('No hay diagnósticos registrados.', estilo_normal))

    elementos.append(Spacer(1, 0.5*cm))
    elementos.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#cccccc')))
    elementos.append(Spacer(1, 0.2*cm))
    elementos.append(Paragraph(
        'Documento generado automáticamente por el Sistema ICATOM — Confidencial',
        estilo_subtitulo
    ))

    doc.build(elementos)
    buffer.seek(0)
    return buffer