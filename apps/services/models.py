from django.db import models


class ServiceCategory(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True, help_text="Icon class name")
    base_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Service Categories"


SERVICE_PACKAGES = [
    {'name': 'Portrait Session', 'description': 'Individual or couple portrait photography (2 hrs)', 'base_price': 2500},
    {'name': 'Event Coverage', 'description': 'Full event photography coverage (4-8 hrs)', 'base_price': 8000},
    {'name': 'Wedding Photography', 'description': 'Complete wedding day coverage', 'base_price': 25000},
    {'name': 'Product Photography', 'description': 'E-commerce and product shoots', 'base_price': 3000},
    {'name': 'Corporate Headshots', 'description': 'Professional business headshots', 'base_price': 1500},
    {'name': 'Baby & Newborn', 'description': 'Newborn and baby milestone photography', 'base_price': 4000},
    {'name': 'Pre-Wedding Shoot', 'description': 'Pre-wedding couple photography session', 'base_price': 12000},
    {'name': 'Birthday Parties', 'description': 'Birthday event photography', 'base_price': 5000},
]
