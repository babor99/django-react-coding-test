from django.contrib import admin
from .models import *


# Register your models here.

@admin.register(Variant)
class VariantAdmin(admin.ModelAdmin):
	list_display = [field.name for field in Variant._meta.fields]


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
	list_display = [field.name for field in Product._meta.fields]


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
	list_display = [field.name for field in ProductImage._meta.fields]


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
	list_display = [field.name for field in ProductVariant._meta.fields]


@admin.register(ProductVariantPrice)
class ProductVariantPriceAdmin(admin.ModelAdmin):
	list_display = [field.name for field in ProductVariantPrice._meta.fields]


