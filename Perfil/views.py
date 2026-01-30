import io
import requests
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from django.template.loader import get_template
from django.views.decorators.clickjacking import xframe_options_exempt # <--- IMPORTANTE
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

# --- VISTA TÚNEL MEJORADA ---
@xframe_options_exempt # <--- ESTO PERMITE QUE SE VEA EN EL IFRAME SIN BLOQUEOS
def ver_archivo(request):
    url = request.GET.get('url')
    if not url:
        return HttpResponse("No se proporcionó URL", status=400)
    
    try:
        # Stream=True es vital para no cargar archivos gigantes en memoria RAM
        response = requests.get(url, stream=True, timeout=15)
        
        if response.status_code == 200:
            content_type = response.headers.get('Content-Type', 'application/pdf')
            
            # StreamingHttpResponse es mejor para archivos en Render
            from django.http import StreamingHttpResponse
            django_response = StreamingHttpResponse(
                response.iter_content(chunk_size=8192), 
                content_type=content_type
            )
            
            django_response['Content-Disposition'] = 'inline'
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
        return HttpResponse("Error: Falta template", status=500)

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