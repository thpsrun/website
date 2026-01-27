from django.db import models


class CountryCodes(models.Model):
    class Meta:
        verbose_name_plural = "Country Codes"
        ordering = ["name"]

    id = models.CharField(
        max_length=10,
        primary_key=True,
        verbose_name="Country Code ID",
    )
    name = models.CharField(
        max_length=50,
        verbose_name="Country Name",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
    )
    updated_at = models.DateTimeField(
        auto_now=True,
    )

    def __str__(self):
        return self.name
