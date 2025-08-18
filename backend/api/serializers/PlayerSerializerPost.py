from typing import Union

from rest_framework import serializers
from srl.models import Players


class PlayerSerializerPost(serializers.ModelSerializer):
    """Serializer for POST'ing player metadata..

    This serializer is used to POST structured information about a specific player.

    SerializerMethodField:
        - ex_stream (bool): Contains information on how to set `ex_stream` for the player.
    """

    ex_stream = serializers.BooleanField()
    nickname = serializers.CharField()

    def validate_ex_stream(
        self,
        ex_stream: Union[bool, str] = None,
    ) -> bool:
        """Validates if the ex_stream field is properly setup."""
        if isinstance(ex_stream, bool):
            return ex_stream
        elif ex_stream == "True":
            return True
        elif ex_stream == "False":
            return False
        else:
            raise serializers.ValidationError("ex_stream is a boolean True or False.")

    def validate_nickname(
        self,
        nickname: str = None,
    ) -> str:
        """Validates if the nickname field is properly setup."""
        if not nickname:
            return
        elif len(nickname) > 30:
            raise serializers.ValidationError(
                "nickname field must be 30 characters or less."
            )
        else:
            return nickname

    class Meta:
        model = Players
        fields = ["ex_stream", "nickname"]
