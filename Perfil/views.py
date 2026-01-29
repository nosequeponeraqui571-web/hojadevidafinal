import io
import requests
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
from pypdf import PdfWriter, PdfReader 

from Perfil.models import (
    DatosPersonales, ExperienciaLaboral, 
    CursosRealizados, Reconocimientos, 
    ProductosAcademicos, ProductosLaborales, VentaGarage
)

def get_active_profile():
    # Obtiene el primer perfil marcado como activo (1)
    return DatosPersonales.objects.filter(perfilactivo=1).first()

def home(request):
    perfil = get_active_profile()
    
    # Si no hay perfil, renderizamos la plantilla vacía o con datos nulos
    if not perfil:
        return render(request, 'hoja_vida.html', {'perfil': None})

    # Preparamos el contexto con TODA la información para la página única
    # Filtramos por el perfil activo y si el item está marcado para verse en el front
    context = {
        'perfil': perfil,
        'experiencias': ExperienciaLaboral.objects.filter(
            idperfilconqueestaactivo=perfil, 
            activarparaqueseveaenfront=True
        ).order_by('-fechainiciogestion'),
        
        'cursos': CursosRealizados.objects.filter(
            idperfilconqueestaactivo=perfil, 
            activarparaqueseveaenfront=True
        ).order_by('-fechafin'),
        
        'reconocimientos': Reconocimientos.objects.filter(
            idperfilconqueestaactivo=perfil, 
            activarparaqueseveaenfront=True
        ).order_by('-fechareconocimiento'),
        
        'productos_academicos': ProductosAcademicos.objects.filter(
            idperfilconqueestaactivo=perfil, 
            activarparaqueseveaenfront=True
        ),
        
        'productos_laborales': ProductosLaborales.objects.filter(
            idperfilconqueestaactivo=perfil, 
            activarparaqueseveaenfront=True
        ).order_by('-fechaproducto'),
        
        'venta_garage': VentaGarage.objects.filter(
            idperfilconqueestaactivo=perfil, 
            activarparaqueseveaenfront=True
        )
    }
    
    # Renderizamos el nuevo archivo único
    return render(request, 'hoja_vida.html', context)

def pdf_datos_personales(request):
    """
    Generación de PDF combinando HTML y adjuntos (imágenes/PDFs externos).
    """
    perfil = get_object_or_404(DatosPersonales, perfilactivo=1)

    # Obtenemos parámetros GET para saber qué incluir (por defecto todo si no se especifica)
    # Nota: Si usas el botón directo del HTML Tron, puedes ajustar esto.
    # Por ahora asumo que quieres exportar todo si no hay filtros.
    incl_exp = request.GET.get('exp', 'true') == 'true'
    incl_cursos = request.GET.get('cursos', 'true') == 'true'
    incl_logros = request.GET.get('logros', 'true') == 'true'
    incl_proy = request.GET.get('proy', 'true') == 'true'
    incl_garage = request.GET.get('garage', 'true') == 'true'

    experiencias = ExperienciaLaboral.objects.filter(idperfilconqueestaactivo=perfil, activarparaqueseveaenfront=True) if incl_exp else []
    cursos_objs = CursosRealizados.objects.filter(idperfilconqueestaactivo=perfil, activarparaqueseveaenfront=True) if incl_cursos else []
    reco_objs = Reconocimientos.objects.filter(idperfilconqueestaactivo=perfil, activarparaqueseveaenfront=True) if incl_logros else []
    garage_items = VentaGarage.objects.filter(idperfilconqueestaactivo=perfil, activarparaqueseveaenfront=True) if incl_garage else []
    
    academicos = ProductosAcademicos.objects.filter(idperfilconqueestaactivo=perfil, activarparaqueseveaenfront=True) if incl_proy else []
    laborales = ProductosLaborales.objects.filter(idperfilconqueestaactivo=perfil, activarparaqueseveaenfront=True) if incl_proy else []

    # IMPORTANTE: Asegúrate de tener un template 'cv_pdf_maestro.html' para el diseño del PDF
    # Si no lo tienes, el PDF fallará.
    try:
        template = get_template('cv_pdf_maestro.html')
    except:
        return HttpResponse("Error: Falta el template 'cv_pdf_maestro.html' para generar el PDF.", status=500)

    html = template.render({
        'perfil': perfil, 
        'items': experiencias, 
        'productos': academicos,
        'productos_laborales': laborales, 
        'cursos': cursos_objs, 
        'reconocimientos': reco_objs,
        'garage': garage_items,
        'incl_experiencia': incl_exp,
        'incl_proyectos': incl_proy,
        'incl_cursos': incl_cursos,
        'incl_logros': incl_logros,
        'incl_garage': incl_garage
    })
    
    buffer_cv = io.BytesIO()
    pisa.CreatePDF(io.BytesIO(html.encode("UTF-8")), dest=buffer_cv)

    writer = PdfWriter()
    buffer_cv.seek(0)
    try:
        reader_base = PdfReader(buffer_cv)
        for page in reader_base.pages:
            writer.add_page(page)
    except:
        pass

    def pegar_certificados(queryset, nombre_campo):
        for obj in queryset:
            archivo = getattr(obj, nombre_campo, None)
            if archivo and hasattr(archivo, 'url'):
                try:
                    r = requests.get(archivo.url, timeout=15)
                    if r.status_code == 200:
                        # Aquí podrías validar si es PDF o Imagen antes de adjuntar
                        writer.append(io.BytesIO(r.content))
                except Exception as e:
                    print(f"Error pegando certificado: {e}")
                    continue

    if incl_exp: pegar_certificados(experiencias, 'rutacertificado')
    if incl_cursos: pegar_certificados(cursos_objs, 'rutacertificado')
    if incl_logros: pegar_certificados(reco_objs, 'rutacertificado')
    if incl_garage: pegar_certificados(garage_items, 'documento_interes')

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="Portafolio_{perfil.apellidos}.pdf"'
    writer.write(response)
    writer.close()
    
    return response