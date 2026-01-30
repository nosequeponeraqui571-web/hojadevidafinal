import io
import requests
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, StreamingHttpResponse
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

# --- VISTA TÚNEL CORREGIDA ---
@xframe_options_exempt
def ver_archivo(request):
    url = request.GET.get('url')
    if not url:
        return HttpResponse("No se proporcionó URL", status=400)
    
    try:
        # Hacemos la petición a Cloudinary
        response = requests.get(url, stream=True, timeout=15)
        
        if response.status_code == 200:
            # Determinamos el tipo de contenido
            content_type = response.headers.get('Content-Type', '')
            
            # Si Cloudinary no nos dice que es PDF, forzamos la detección si parece uno
            if 'pdf' not in content_type and ('.pdf' in url.lower() or 'image/upload' in url):
                 # A veces Cloudinary devuelve octet-stream, forzamos PDF si es para el visor
                 content_type = 'application/pdf'

            # Usamos StreamingHttpResponse para eficiencia
            django_response = StreamingHttpResponse(
                response.iter_content(chunk_size=8192), 
                content_type=content_type
            )
            
            # --- EL TRUCO CLAVE ---
            # Forzamos filename="archivo.pdf" para que Chrome active el visor interno
            django_response['Content-Disposition'] = 'inline; filename="visualizacion.pdf"'
            
            # Aseguramos que se permita en iframe
            django_response['X-Frame-Options'] = 'SAMEORIGIN'
            
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