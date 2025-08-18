from rest_framework import serializers
from srl.models import Awards


class AwardSerializer(serializers.ModelSerializer):
    """Serializer for awards metadata."""

    class Meta:
        model = Awards
        fields = ["name"]
