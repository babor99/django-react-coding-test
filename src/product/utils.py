import uuid
from io import BytesIO
from PIL import Image

from django.conf import settings
from django.core.files.storage import FileSystemStorage


def parse_request_data(data: object)-> tuple:
    images = []
    productvariants = []
    productvariant_prices = []

    for key, value in data.items():
        if key.startswith('image'):
            images.append(value)

    for i in range(len(data) // 3):
        if data.get(f'productVariantPrices[{i}][title]'):
            productvariant_prices.append({'title': data.get(f'productVariantPrices[{i}][title]'), 'price': data.get(f'productVariantPrices[{i}][price]'), 'stock': data.get(f'productVariantPrices[{i}][stock]')}) 
        if data.get(f'productVariants[{i}][variant]'):
            productVariant = {'variant': data.get(f'productVariants[{i}][variant]'), 'tags': []}
            j = 0
            while j >= 0:
                productVariant['tags'].append(data.get(f'productVariants[{i}][tags][{j}]'))
                if data.get(f'productVariants[{i}][tags][{j+1}]'):
                    j += 1
                else:
                    j = -1
            productvariants.append(productVariant)

    return (images, productvariants, productvariant_prices)


def get_variant_id(productvariants: dict, tag: str)-> int:
    for item in productvariants:
        if tag in item['tags']:
            return item['variant']
    return 0


def save_productimage(productimage_obj: object, image_file: object)-> None:
    filename = str(productimage_obj.id) + str(uuid.uuid4())

    image = Image.open(image_file)

    # Converting the image to JPEG format and save it to buffer
    buffer = BytesIO()
    image.save(buffer, format='JPEG')
    buffer.seek(0)

    # Save the image file to the server
    storage = FileSystemStorage(location=settings.MEDIA_ROOT)
    path = storage.save(filename+'.jpeg', buffer)

    # Update the `file_path` field of the `ProductImage` object with the URL where the image can be accessed
    productimage_obj.file_path = storage.url(path)
    productimage_obj.save()
