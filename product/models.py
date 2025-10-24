from django.db import models


class ProductCategory(models.Model):

    category = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.category


class Product(models.Model):

    name = models.CharField(max_length=255)
    category = models.ForeignKey(ProductCategory, on_delete=models.CASCADE)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    old_price = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, null=True
    )
    product_image = models.ImageField(upload_to="products/")
    product_stock = models.PositiveIntegerField(default=0)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
