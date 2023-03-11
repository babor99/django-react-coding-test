from django.db import models
from django.core.files.storage import FileSystemStorage

from config.g_model import TimeStampMixin


# Create your models here.
class Variant(TimeStampMixin):
    title = models.CharField(max_length=40, unique=True)
    description = models.TextField()
    active = models.BooleanField(default=True)
    def __str__(self) -> str:
        return f"<Variant{self.id}:{self.title}>"


class Product(TimeStampMixin):
    title = models.CharField(max_length=255)
    sku = models.SlugField(max_length=255, unique=True)
    description = models.TextField()
    def __str__(self) -> str:
        return f'<Product{self.id}:{self.title[:15]}>'


class ProductImage(TimeStampMixin):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    file_path = models.URLField()

    def __str__(self) -> str:
        return f"<ProductImage{self.id}: {self.product.title[:10]}>"

    def delete(self, *args, **kwargs):
        # Get the file path from the file URL
        storage = FileSystemStorage()
        file_path = storage.path(self.file_path.replace(storage.base_url, ''))

        # Delete the file from the server
        storage.delete(file_path)

        # Call the superclass delete method to delete the object
        super(ProductImage, self).delete(*args, **kwargs)


class ProductVariant(TimeStampMixin):
    variant_title = models.CharField(max_length=255)
    variant = models.ForeignKey(Variant, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='productvariant')
    def __str__(self) -> str:
        return f"<ProductVariant{self.id}: {self.variant_title}>"


class ProductVariantPrice(TimeStampMixin):
    product_variant_one = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, null=True,
                                            related_name='product_variant_one')
    product_variant_two = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, null=True,
                                            related_name='product_variant_two')
    product_variant_three = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, null=True,
                                              related_name='product_variant_three')
    price = models.FloatField(default=0)
    stock = models.FloatField(default=0)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='productvariantprice')

    class Meta:
        unique_together = [('product', 'product_variant_one', 'product_variant_two', 'product_variant_three')]

    def __str__(self) -> str:
        return f"<ProductVariantPrice{str(self.id)}: {self.product.title[:10]}>"
