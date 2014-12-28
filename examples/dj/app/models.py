from django.db import models

# Create your models here.

class Cat(models.Model):
    SIZE = (
        ('Big', 2),
        ('Medium', 1),
        ('Small', 0),
    )

    happy = models.BooleanField(default=True)
    size = models.IntegerField(choices=SIZE)
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name