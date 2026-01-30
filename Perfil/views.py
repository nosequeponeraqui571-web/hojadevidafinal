import io
import requests
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, StreamingHttpResponse
from django.template.loader import get_template
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

# --- NUEVA VISTA PARA EL TÚNEL DE ARCHIVOS ---
def ver_archivo(request):
    """
    Esta vista actúa como un proxy. Descarga el archivo de Cloudinary (o donde sea)
    y lo sirve desde el propio dominio de la aplicación para evitar bloqueos CORS/Iframe.
    """
    url = request.GET.get('url')
    if not url:
        return HttpResponse("No se proporcionó URL", status=400)
    
    try:
        # Hacemos la petición al servidor externo (Cloudinary)
        response = requests.get(url, stream=True, timeout=10)
        
        if response.status_code == 200:
            # Obtenemos el tipo de contenido original (application/pdf, image/png, etc.)
            content_type = response.headers.get('Content-Type', 'application/pdf')
            
            # Servimos el contenido directamente
            # Usamos HttpResponse con el contenido en bytes
            django_response = HttpResponse(response.content, content_type=content_type)
            
            # Forzamos que se muestre en línea (no descargar)
            django_response['Content-Disposition'] = 'inline'
            # Eliminamos restricciones de frame para esta respuesta específica si existieran
            django_response['X-Frame-Options'] = 'SAMEORIGIN'
            
            return django_response
        else:
            return HttpResponse(f"Error al obtener el archivo remoto: {response.status_code}", status=404)
            
    except Exception as e:
        return HttpResponse(f"Error interno del servidor: {str(e)}", status=500)

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
        return HttpResponse("Error: Falta el template 'cv_pdf_maestro.html'", status=500)

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