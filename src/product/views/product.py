from django.views import generic
from django.http import Http404
from django.db.models import CharField, Value, F
from django.db.models.functions import Concat
from django.contrib.postgres.aggregates import ArrayAgg

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from product.models import Product, Variant, ProductVariant, ProductVariantPrice, ProductImage
from product.serializers import ProductSerializer, ProductImageSerializer
from product.utils import get_variant_id, paginate_data




class ListProductView(generic.ListView):
    template_name = 'products/list.html'
    model = Product
    paginate_by = 3

    def get_queryset(self):
        print('self.request.GET: ', self.request.GET)
        query_dict = self.request.GET
        restricted_values = ('', ' ', None, '0', 'undefined')
        product_filter_dict = dict()

        title = query_dict.get('title', None)
        date = query_dict.get('date', None)
        variant_title = query_dict.get('variant', None)
        price_from = query_dict.get('price_from', None)
        price_to = query_dict.get('price_to', None)

        if title:
            product_filter_dict['title__icontains'] = title
        if date:
            product_filter_dict['created_at__date'] = date

        if variant_title not in restricted_values:
            product_filter_dict['productvariant__variant_title'] = variant_title

        if price_from not in restricted_values or price_to not in restricted_values:
            if price_from not in restricted_values:
                product_filter_dict['productvariantprice__price__gte'] = float(price_from)
            if price_to not in restricted_values:
                product_filter_dict['productvariantprice__price__lte'] = float(price_to)

        products = Product.objects.filter(**product_filter_dict).order_by('id').distinct('id').prefetch_related('productvariantprice')
        print('products: ', products)
        print('product_filter_dict: ', product_filter_dict)

        return products

    def get_context_data(self, **kwargs):
        product_variants = ProductVariant.objects.order_by('variant_title').distinct('variant_title').values('variant__title', 'variant_title')

        # Group the variants by their variant titles
        grouped_variants = {}
        for variant in product_variants:
            if variant['variant__title'] not in grouped_variants:
                grouped_variants[variant['variant__title']] = []
            grouped_variants[variant['variant__title']].append(variant)

        # Build the data_variants list in the desired format
        data_variants = []
        for title, variants in grouped_variants.items():
            group = {'label': title, 'options': []}
            for variant in variants:
                group['options'].append({'value': variant['variant_title'], 'label': variant['variant_title']})
            data_variants.append(group)

        current_page = int(self.request.GET.get('page', 1))
        print('current_page: ', current_page)
    
        context = super(ListProductView, self).get_context_data(**kwargs)
        context['product'] = True
        context['product_start'] = ((current_page - 1) * self.paginate_by) + 1
        context['product_end'] = current_page * self.paginate_by
        context['productvariants'] = data_variants
        return context




class CreateProductView(generic.TemplateView):
    template_name = 'products/create.html'

    def get_context_data(self, **kwargs):
        context = super(CreateProductView, self).get_context_data(**kwargs)
        variants = Variant.objects.filter(active=True).values('id', 'title')
        context['variants'] = list(variants.all())
        return context




# BELOW ARE API VIEWS

class GetUpdateProductAPIView(APIView):

    def get_object(self, pk):
        try:
            return Product.objects.get(pk=pk)
        except Product.DoesNotExist:
            raise Http404


    def get(self, request, pk, format=None):
        product_obj = self.get_object(pk)
        product_serializer = ProductSerializer(product_obj)

        productimage_objs = ProductImage.objects.filter(product=product_obj)
        productimage_serializer = ProductImageSerializer(productimage_objs, many=True)

        productvariants = ProductVariant.objects.filter(product=product_obj).values('variant').annotate(tags=ArrayAgg(F('variant_title'), distinct=True))
        # print('productvariants: ', productvariants)

        productvariant_prices = ProductVariantPrice.objects.filter(product=product_obj).annotate(title=Concat('product_variant_one__variant_title', Value('/'), 'product_variant_two__variant_title', Value('/'), 'product_variant_three__variant_title', Value('/'), output_field=CharField())).values('id', 'title', 'price', 'stock')
        print('productvariant_prices: ', productvariant_prices)

        return Response({'product': product_serializer.data, 'productimages': productimage_serializer.data, 'productvariants': productvariants, 'productvariant_prices': productvariant_prices}, status=status.HTTP_200_OK)




class CreateProductAPIView(APIView):
    pass



class ProductImageAPIView(APIView):
    pass


