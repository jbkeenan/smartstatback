from django.urls import path, include
from django.contrib import admin
from django.views.generic import TemplateView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    path('business-analysis/', TemplateView.as_view(template_name='business_analysis.html'), name='business_analysis'),
]
