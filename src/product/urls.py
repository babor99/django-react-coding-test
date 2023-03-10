from django.urls import path
from django.views.generic import TemplateView

from product.views.product import CreateProductView, ListProductView, GetUpdateProductAPIView, CreateProductAPIView, ProductImageAPIView
from product.views.variant import VariantView, VariantCreateView, VariantEditView

app_name = "product"

urlpatterns = [
    # Variants URLs
    path('variants/', VariantView.as_view(), name='variants'),
    path('variant/create', VariantCreateView.as_view(), name='create.variant'),
    path('variant/<int:id>/edit', VariantEditView.as_view(), name='update.variant'),

    # Products URLs
    path('list/', ListProductView.as_view(), name='list.product'),
    path('createorupdate/<str:pk>', CreateProductView.as_view(), name='create.product'), # for rendering the create-update product page
    # API VIEW'S URLS
    path('api/v1/product/<int:pk>', GetUpdateProductAPIView.as_view()),

]