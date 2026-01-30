import io
import requests
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from django.template.loader import get_template
from django.views.decorators.clickjacking import xframe_options_exempt
from xhtml2pdf import pisa
from pypdf import PdfWriter, PdfReader 

from Perfil.models import (
    DatosPersonales, ExperienciaLaboral, 
    CursosRealizados, Reconocimientos, 
    ProductosAcademicos, ProductosLaborales, VentaGarage
)

def get_active_profile():
    return DatosPersonales.objects.filter(perfilactivo=1).first()

def home(request):
    perfil = get_active_profile()
    if not perfil:
        return render(request, 'hoja_vida.html', {'perfil': None})

    context = {
        'perfil': perfil,
        'experiencias': ExperienciaLaboral.objects.filter(idperfilconqueestaactivo=perfil, activarparaqueseveaenfront=True).order_by('-fechainiciogestion'),
        'cursos': CursosRealizados.objects.filter(idperfilconqueestaactivo=perfil, activarparaqueseveaenfront=True).order_by('-fechafin'),
        'reconocimientos': Reconocimientos.objects.filter(idperfilconqueestaactivo=perfil, activarparaqueseveaenfront=True).order_by('-fechareconocimiento'),
        'productos_academicos': ProductosAcademicos.objects.filter(idperfilconqueestaactivo=perfil, activarparaqueseveaenfront=True),
        'productos_laborales': ProductosLaborales.objects.filter(idperfilconqueestaactivo=perfil, activarparaqueseveaenfront=True).order_by('-fechaproducto'),
        'venta_garage': VentaGarage.objects.filter(idperfilconqueestaactivo=perfil, activarparaqueseveaenfront=True)
    }
    return render(request, 'hoja_vida.html', context)

# --- VISTA TÚNEL VERSIÓN ROBUSTA ---
@xframe_options_exempt
def ver_archivo(request):
    """
    Descarga el archivo completo en memoria y lo sirve con Content-Length.
    Esto es más compatible con visores PDF de navegadores que el Streaming.
    """
    url = request.GET.get('url')
    if not url:
        return HttpResponse("No se proporcionó URL", status=400)
    
    try:
        # Petición estándar (sin stream=True) para obtener todo el contenido
        response = requests.get(url, timeout=20)
        
        if response.status_code == 200:
            content_type = response.headers.get('Content-Type', '')
            
            # Forzar tipo PDF si la URL o el tipo original lo sugieren
            if 'pdf' not in content_type and ('.pdf' in url.lower() or 'image/upload' in url):
                 content_type = 'application/pdf'

            # Servimos el archivo usando HttpResponse estándar
            # Esto permite que Django calcule el Content-Length automáticamente
            django_response = HttpResponse(response.content, content_type=content_type)
            
            # Forzamos nombre de archivo y disposición inline
            django_response['Content-Disposition'] = 'inline; filename="documento_visualizacion.pdf"'
            
            # Encabezados de seguridad permisivos para el iframe
            django_response['X-Frame-Options'] = 'SAMEORIGIN'
            
            # IMPORTANTE: Asegurar que se envía el tamaño
            django_response['Content-Length'] = len(response.content)
            
            return django_response
        else:
            return HttpResponse(f"Error remoto: {response.status_code}", status=404)
            
    except Exception as e:
        return HttpResponse(f"Error servidor: {str(e)}", status=500)

def pdf_datos_personales(request):
    perfil = get_object_or_404(DatosPersonales, perfilactivo=1)
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

    try:
        template = get_template('cv_pdf_maestro.html')
    except:
        return HttpResponse("Error: Falta template cv_pdf_maestro.html", status=500)

    html = template.render({
        'perfil': perfil, 'items': experiencias, 'productos': academicos,
        'productos_laborales': laborales, 'cursos': cursos_objs, 'reconocimientos': reco_objs,
        'garage': garage_items, 'incl_experiencia': incl_exp, 'incl_proyectos': incl_proy,
        'incl_cursos': incl_cursos, 'incl_logros': incl_logros, 'incl_garage': incl_garage
    })
    
    buffer_cv = io.BytesIO()
    pisa.CreatePDF(io.BytesIO(html.encode("UTF-8")), dest=buffer_cv)

    writer = PdfWriter()
    buffer_cv.seek(0)
    try:
        reader_base = PdfReader(buffer_cv)
        for page in reader_base.pages:
            writer.add_page(page)
    except: pass

    def pegar_certificados(queryset, nombre_campo):
        for obj in queryset:
            archivo = getattr(obj, nombre_campo, None)
            if archivo and hasattr(archivo, 'url'):
                try:
                    r = requests.get(archivo.url, timeout=15)
                    if r.status_code == 200:
                        writer.append(io.BytesIO(r.content))
                except: continue

    if incl_exp: pegar_certificados(experiencias, 'rutacertificado')
    if incl_cursos: pegar_certificados(cursos_objs, 'rutacertificado')
    if incl_logros: pegar_certificados(reco_objs, 'rutacertificado')
    if incl_garage: pegar_certificados(garage_items, 'documento_interes')

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="Portafolio_{perfil.apellidos}.pdf"'
    writer.write(response)
    writer.close()
    return response