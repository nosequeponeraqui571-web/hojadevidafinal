from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from Perfil import views 

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Ruta principal que carga la Single Page Application (hoja_vida.html)
    path('', views.home, name='home'),
    
    # Ruta para generar el PDF
    path('exportar-cv-completo/', views.pdf_datos_personales, name='exportar_cv'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)