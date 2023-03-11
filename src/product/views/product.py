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
from product.utils import get_variant_id, save_productimage, parse_request_data




class ListProductView(generic.ListView):
    template_name = 'products/list.html'
    model = Product
    paginate_by = 5

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

        productvariant_prices = ProductVariantPrice.objects.order_by('id').filter(product=product_obj).annotate(title=Concat('product_variant_one__variant_title', Value('/'), 'product_variant_two__variant_title', Value('/'), 'product_variant_three__variant_title', Value('/'), output_field=CharField())).values('id', 'title', 'price', 'stock')
        print('productvariant_prices: ', productvariant_prices)

        return Response({'product': product_serializer.data, 'productimages': productimage_serializer.data, 'productvariants': productvariants, 'productvariant_prices': productvariant_prices}, status=status.HTTP_200_OK)


    def put(self, request, pk, format=None):
        data = request.data
        product_dict = {}
        images = []
        productvariants = []
        productvariant_prices = []
        print('data: ', data)
        print('len data: ', len(data))

        product_dict['title'] = data.get('title', '')
        product_dict['sku'] = data.get('sku', '')
        product_dict['description'] = data.get('description', '')

        images, productvariants, productvariant_prices = parse_request_data(data)

        print('images: ',  images)
        print('productVariants: ', productvariants)
        print('productVariantPrices: ', productvariant_prices)

        product_obj = self.get_object(pk)

        # update basic product data
        serializer = ProductSerializer(product_obj, data=product_dict)
        if serializer.is_valid():
            serializer.save()

            # create new images
            for image in images:
                product_image = ProductImage.objects.create(product=product_obj, file_path='')
                save_productimage(product_image, image)

            # create or update product variant prices
            for variant_price in productvariant_prices:
                variant_titles = variant_price['title'].split('/')
                productvariant_one, one_created = None, False
                productvariant_two, two_created = None, False
                productvariant_three, three_created = None, False
                productvariant_list = []
                created_list = []
                for i, variant_title in enumerate(variant_titles):
                    if variant_title:
                        variant_id = None

                        #get variant_id from variant obj whose tags include the current variant_title
                        for productvariant in productvariants:
                            if variant_title in productvariant['tags']:
                                variant_id = productvariant['variant']

                        # if variant_id exist, then get the ProductVariant object
                        if variant_id:
                            print(f"i={i}, product={product_obj.id}, variant_id={variant_id}, variant_title={variant_title}")
                            if i == 0:
                                productvariant_one, one_created = ProductVariant.objects.get_or_create(product=product_obj, variant_id=variant_id, variant_title=variant_title)
                                productvariant_list.append(productvariant_one.variant_title)
                                if one_created:
                                    created_list.append('one')
                            if i == 1:
                                productvariant_two, two_created = ProductVariant.objects.get_or_create(product=product_obj, variant_id=variant_id, variant_title=variant_title)
                                productvariant_list.append(productvariant_two.variant_title)
                                if two_created:
                                    created_list.append('two')
                            if i == 2:
                                productvariant_three, three_created = ProductVariant.objects.get_or_create(product=product_obj, variant_id=variant_id, variant_title=variant_title)
                                productvariant_list.append(productvariant_three.variant_title)
                                if three_created:
                                    created_list.append('three')

                print('productvariant_list: ', productvariant_list)
                productvariantprice_obj = None
                if 'one' in created_list and 'two' in created_list and 'three' in created_list:
                    print('inside one two three created')
                    ProductVariantPrice.objects.create(
                        product=product_obj,
                        product_variant_one=productvariant_one,
                        product_variant_two=productvariant_two,
                        product_variant_three=productvariant_three,
                        price=variant_price['price'],
                        stock=variant_price['stock'],
                    )
                elif 'one' in created_list and 'two' in created_list:
                    print('inside one two created')
                    ProductVariantPrice.objects.create(
                        product=product_obj,
                        product_variant_one=productvariant_one,
                        product_variant_two=productvariant_two,
                        price=variant_price['price'],
                        stock=variant_price['stock'],
                    )
                elif 'one' in created_list:
                    print('inside one created')
                    ProductVariantPrice.objects.create(
                        product=product_obj,
                        product_variant_one=productvariant_one,
                        price=variant_price['price'],
                        stock=variant_price['stock'],
                    )
                elif 'two' in created_list and 'three' in created_list:
                    print('inside two three created')
                    productvariantprice_obj = ProductVariantPrice.objects.filter(
                        product=product_obj,
                        product_variant_one__variant_title__in=productvariant_list,
                    ).first()
                    productvariantprice_obj.product_variant_two = productvariant_two
                    productvariantprice_obj.product_variant_three = productvariant_three
                elif 'two' in created_list:
                    print('inside two created')
                    productvariantprice_obj = ProductVariantPrice.objects.filter(
                        product=product_obj,
                        product_variant_one__variant_title__in=productvariant_list,
                    ).first()
                    productvariantprice_obj.product_variant_two = productvariant_two
                    productvariantprice_obj.product_variant_three = productvariant_three
                elif 'three' in created_list:
                    print('inside three created')
                    productvariantprice_obj = ProductVariantPrice.objects.filter(
                        product=product_obj,
                        product_variant_one__variant_title__in=productvariant_list,
                        product_variant_two__variant_title__in=productvariant_list,
                    ).first()
                    productvariantprice_obj.product_variant_three = productvariant_three

                else:
                    print('inside 0 created')
                    print('created_list: ', created_list)
                    if productvariant_one and productvariant_two and productvariant_three:
                        print('inside one two three retrieved')
                        try:
                            print('inside first try!')
                            productvariantprice_obj = ProductVariantPrice.objects.get(
                                product=product_obj,
                                product_variant_one__variant_title__in=productvariant_list,
                                product_variant_two__variant_title__in=productvariant_list,
                                product_variant_three__variant_title__in=productvariant_list,
                            )
                            print('inside first try executed!')
                        except ProductVariantPrice.DoesNotExist:
                            print('inside first try does not exist!')
                            try:
                                print('inside second try get!!')
                                productvariantprice_obj = ProductVariantPrice.objects.get(
                                    product=product_obj,
                                    product_variant_one__variant_title__in=productvariant_list,
                                    product_variant_two__variant_title__in=productvariant_list,
                                )
                                productvariantprice_obj.product_variant_three = productvariant_three
                                print('inside second try get executed!!')
                            except ProductVariantPrice.MultipleObjectsReturned:
                                print('inside second try  multiple objects returned!!!')
                                ProductVariantPrice.objects.create(
                                    product=product_obj,
                                    product_variant_one=productvariant_one,
                                    product_variant_two=productvariant_two,
                                    product_variant_three=productvariant_three,
                                    price=variant_price['price'],
                                    stock=variant_price['stock'],
                                )
                            except ProductVariantPrice.DoesNotExist:
                                print('inside second try  multiple objects returned!!!')
                                ProductVariantPrice.objects.create(
                                    product=product_obj,
                                    product_variant_one=productvariant_one,
                                    product_variant_two=productvariant_two,
                                    product_variant_three=productvariant_three,
                                    price=variant_price['price'],
                                    stock=variant_price['stock'],
                                )
                                print('inside second try  multiple objects returned executed!!!')

                        print('inside one two three retrieved executed')
                    elif productvariant_one and productvariant_two:
                        print('inside one two retrieved')
                        try:
                            productvariantprice_obj = ProductVariantPrice.objects.get(
                                product=product_obj,
                                product_variant_one__variant_title__in=productvariant_list,
                                product_variant_two__variant_title__in=productvariant_list,
                            )
                        except ProductVariantPrice.DoesNotExist:
                            try:
                                productvariantprice_obj = ProductVariantPrice.objects.get(
                                    product=product_obj,
                                    product_variant_one__variant_title__in=productvariant_list,
                                )
                                productvariantprice_obj.product_variant_two = productvariant_two
                            except ProductVariantPrice.MultipleObjectsReturned:
                                ProductVariantPrice.objects.create(
                                    product=product_obj,
                                    product_variant_one=productvariant_one,
                                    product_variant_two=productvariant_two,
                                    price=variant_price['price'],
                                    stock=variant_price['stock'],
                                )
                        print('inside one two retrieved executed')
                    elif productvariant_one:
                        print('inside one retrieved')
                        try:
                            productvariantprice_obj = ProductVariantPrice.objects.get(
                                product=product_obj,
                                product_variant_one__variant_title__in=productvariant_list,
                            )
                        except ProductVariantPrice.DoesNotExist:
                            ProductVariantPrice.objects.create(
                                product=product_obj,
                                product_variant_one=productvariant_one,
                                price=variant_price['price'],
                                stock=variant_price['stock'],
                            )
                        print('inside one retrieved executed')

                print('created_list: ', created_list)
                if productvariantprice_obj:
                    productvariantprice_obj.price = variant_price['price']
                    productvariantprice_obj.stock = variant_price['stock']
                    productvariantprice_obj.save()

                print('productvariantlist: ', productvariant_list)
                print('productvariantprice_obj: ', productvariantprice_obj)
        else:
            return Response({'error': serializer.errors, 'message': "Can't update data."}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'message': "Product updated successfully."}, status=status.HTTP_200_OK)




class CreateProductAPIView(APIView):

    def post(self, request, format=None):
        data = request.data
        images = []
        productvariants = []
        productvariant_prices = []
        print('data: ', data)
        print('len data: ', len(data))

        images, productvariants, productvariant_prices = parse_request_data(data)

        print('images: ',  images)
        print('productVariants: ', productvariants)
        print('productVariantPrices: ', productvariant_prices)

        serializer = ProductSerializer(data=data)
        if serializer.is_valid():
            serializer.save()

            product_id = serializer.data['id']
            product_obj = Product.objects.get(id=product_id)

            for image in images:
                product_image = ProductImage.objects.create(product=product_obj, file_path='')
                save_productimage(product_image, image)

            for productvariant_price in productvariant_prices:
                productvariant_price_obj = ProductVariantPrice.objects.create(product=product_obj,price=productvariant_price['price'], stock=productvariant_price['stock'])
                productvariant_obj_list = []
                for tag in productvariant_price['title'].split('/'):
                    variant_id = get_variant_id(productvariants, tag)
                    print('variant_id: ', variant_id)

                    if variant_id:
                        variant_obj = Variant.objects.get(pk=variant_id)
                        productvariant_obj, created = ProductVariant.objects.get_or_create(product=product_obj, variant=variant_obj, variant_title=tag)
                        productvariant_obj_list.append(productvariant_obj)

                productvariant_obj_list_len = len(productvariant_obj_list)

                if productvariant_obj_list_len == 3:
                    productvariant_price_obj.product_variant_one = productvariant_obj_list[0]
                    productvariant_price_obj.product_variant_two = productvariant_obj_list[1]
                    productvariant_price_obj.product_variant_three = productvariant_obj_list[2]
                elif productvariant_obj_list_len == 2:
                    productvariant_price_obj.product_variant_one = productvariant_obj_list[0]
                    productvariant_price_obj.product_variant_two = productvariant_obj_list[1]
                elif productvariant_obj_list_len == 1:
                    productvariant_price_obj.product_variant_one = productvariant_obj_list[0]
                productvariant_price_obj.save()

            print('product_obj: ', product_obj)

            return Response({'data': serializer.data, 'message': 'Product created successfully!'}, status=status.HTTP_201_CREATED)
        else:
            return Response({'error': serializer.errors, 'message': 'Product creation failed!'}, status=status.HTTP_400_BAD_REQUEST)




class ProductImageAPIView(APIView):

    def delete(self, request, pk, format=None):
        try:
            productimage = ProductImage.objects.get(pk=pk)
            productimage.delete()
        except ProductImage.DoesNotExist:
            return Response({'error': "Product image doesn't exist"}, status=status.HTTP_400_BAD_REQUEST)

        return Response({'message': "Product image deleted successfully"}, status=status.HTTP_200_OK)
