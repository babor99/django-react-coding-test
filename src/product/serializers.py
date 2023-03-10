from rest_framework import serializers

from .models import *




class ProductMinimalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'title']



class VariantMinimalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Variant
        fields = ['id', 'title', 'active']



class ProductVariantMinimalSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductVariant
        fields = ['id', 'variant_title', 'variant', 'product']



class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = '__all__'




class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = '__all__'




class ProductVariantSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductVariant
        fields = '__all__'




class ProductVariantPriceListSerializer(serializers.ModelSerializer):
    product_variant_one = ProductVariantMinimalSerializer()
    product_variant_two = ProductVariantMinimalSerializer()
    product_variant_three = ProductVariantMinimalSerializer()
    class Meta:
        model = ProductVariantPrice
        fields = '__all__'




class ProductVariantPriceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductVariantPrice
        fields = '__all__'



