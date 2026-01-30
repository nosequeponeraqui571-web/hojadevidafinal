from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from Perfil import views 

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Ruta principal
    path('', views.home, name='home'),
    
    # Ruta para generar el PDF completo
    path('exportar-cv-completo/', views.pdf_datos_personales, name='exportar_cv'),
    
    # --- NUEVA RUTA DE PROXY ---
    # Esta ruta servirá los archivos evitando el bloqueo de iframes externos
    path('ver-archivo/', views.ver_archivo, name='ver_archivo'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)