from django.db import models
from django.utils.text import slugify

from srl.models.variables import Variables


class VariableValues(models.Model):
    class Meta:
        verbose_name_plural = "Variable Values"
        ordering = ["var__game", "var", "var__scope", "name"]

    var = models.ForeignKey(
        Variables,
        verbose_name="Linked Variable",
        null=True,
        on_delete=models.SET_NULL,
    )
    name = models.CharField(
        max_length=50,
        verbose_name="Name",
    )
    slug = models.SlugField(
        max_length=50,
        verbose_name="Slug",
        blank=True,
    )
    value = models.CharField(
        max_length=10,
        primary_key=True,
        verbose_name="Value ID",
    )
    archive = models.BooleanField(
        verbose_name="Archive Value",
        default=False,
    )
    rules = models.TextField(
        max_length=1000,
        verbose_name="Rules",
        blank=True,
        null=True,
    )

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.var.game.name}: {self.var.name} - {self.name}"
