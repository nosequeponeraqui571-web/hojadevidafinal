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

@xframe_options_exempt
def ver_archivo(request):
    url = request.GET.get('url')
    if not url:
        return HttpResponse("Falta el parámetro URL", status=400)
    
    try:
        response = requests.get(url, timeout=25)
        
        if response.status_code == 200:
            content_type = response.headers.get('Content-Type', '')
            if 'image' not in content_type.lower():
                content_type = 'application/pdf'
            elif 'pdf' in url.lower():
                content_type = 'application/pdf'

            django_response = HttpResponse(response.content, content_type=content_type)
            django_response['Content-Disposition'] = 'inline; filename="documento_visualizacion.pdf"'
            django_response['X-Frame-Options'] = 'SAMEORIGIN'
            django_response['Content-Length'] = len(response.content)
            
            return django_response
        else:
            return HttpResponse(f"Error externo: {response.status_code}", status=404)
            
    except Exception as e:
        return HttpResponse(f"Error servidor: {str(e)}", status=500)

# --- VISTA PDF CORREGIDA ---
def pdf_datos_personales(request):
    perfil = get_object_or_404(DatosPersonales, perfilactivo=1)
    
    # 1. Leer parámetros de la URL (del modal JS)
    req_exp = request.GET.get('exp', 'true') == 'true'
    req_cursos = request.GET.get('cursos', 'true') == 'true'
    req_logros = request.GET.get('logros', 'true') == 'true'
    req_proy = request.GET.get('proy', 'true') == 'true'
    req_garage = request.GET.get('garage', 'false') == 'true'

    # 2. Obtener datos filtrados
    experiencias = ExperienciaLaboral.objects.filter(idperfilconqueestaactivo=perfil, activarparaqueseveaenfront=True).order_by('-fechainiciogestion') if req_exp else []
    cursos_objs = CursosRealizados.objects.filter(idperfilconqueestaactivo=perfil, activarparaqueseveaenfront=True).order_by('-fechafin') if req_cursos else []
    reco_objs = Reconocimientos.objects.filter(idperfilconqueestaactivo=perfil, activarparaqueseveaenfront=True).order_by('-fechareconocimiento') if req_logros else []
    
    academicos = ProductosAcademicos.objects.filter(idperfilconqueestaactivo=perfil, activarparaqueseveaenfront=True) if req_proy else []
    laborales = ProductosLaborales.objects.filter(idperfilconqueestaactivo=perfil, activarparaqueseveaenfront=True).order_by('-fechaproducto') if req_proy else []
    
    garage_items = VentaGarage.objects.filter(idperfilconqueestaactivo=perfil, activarparaqueseveaenfront=True) if req_garage else []

    try:
        template = get_template('cv_pdf_maestro.html')
    except:
        return HttpResponse("Error: Falta template cv_pdf_maestro.html", status=500)

    # 3. Contexto Mapeado Exactamente a tu Plantilla
    # Aquí es donde ocurría el error: los nombres no coincidían.
    context = {
        'perfil': perfil,
        
        # Listas de datos (Nombres usados en el for loop de tu HTML)
        'items': experiencias,          # Tu html usa: {% for item in items %}
        'cursos': cursos_objs,          # Tu html usa: {% for curso in cursos %}
        'reconocimientos': reco_objs,   # Tu html usa: {% for rec in reconocimientos %}
        'productos': academicos,        # Tu html usa: {% for prod in productos %}
        'productos_laborales': laborales, 
        'garage': garage_items,
        
        # Banderas de control (Nombres usados en los IF de tu HTML)
        # IMPORTANTE: Estos deben coincidir con {% if incl_experiencia ... %}
        'incl_experiencia': req_exp and len(experiencias) > 0,
        'incl_cursos': req_cursos and len(cursos_objs) > 0,
        'incl_logros': req_logros and len(reco_objs) > 0,
        'incl_proyectos': req_proy and (len(academicos) > 0 or len(laborales) > 0),
        'incl_garage': req_garage and len(garage_items) > 0,
    }

    html = template.render(context)
    
    buffer_cv = io.BytesIO()
    pisa_status = pisa.CreatePDF(io.BytesIO(html.encode("UTF-8")), dest=buffer_cv)
    
    if pisa_status.err:
        return HttpResponse("Error al generar PDF principal", status=500)

    writer = PdfWriter()
    buffer_cv.seek(0)
    
    try:
        reader_base = PdfReader(buffer_cv)
        for page in reader_base.pages:
            writer.add_page(page)
    except Exception as e:
        return HttpResponse(f"Error leyendo PDF base: {e}", status=500)

    # Pegado de certificados al final
    def pegar_certificados(queryset, nombre_campo):
        for obj in queryset:
            archivo = getattr(obj, nombre_campo, None)
            if archivo and hasattr(archivo, 'url'):
                try:
                    r = requests.get(archivo.url, timeout=15)
                    if r.status_code == 200:
                        # Verificación simple de cabecera PDF
                        if b'%PDF' in r.content[:20]:
                            cert_pdf = io.BytesIO(r.content)
                            reader_cert = PdfReader(cert_pdf)
                            for page in reader_cert.pages:
                                writer.add_page(page)
                except: continue

    if req_exp: pegar_certificados(experiencias, 'rutacertificado')
    if req_cursos: pegar_certificados(cursos_objs, 'rutacertificado')
    if req_logros: pegar_certificados(reco_objs, 'rutacertificado')
    if req_garage: pegar_certificados(garage_items, 'documento_interes')

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="Portafolio_{perfil.apellidos}.pdf"'
    
    writer.write(response)
    writer.close()
    
    return response