from celery import shared_task
from django.db import transaction

from srl.m_tasks import src_api
from srl.models import Platforms
from srl.srcom.schema.src import SrcPlatformModel


@shared_task
def sync_platforms(
    platform_data: str | dict,
) -> None:
    """Creates or updates a `Platforms` model object based on the `platform_data` argument.

    Arguments:
        platform_data (str | dict): Either the unique ID (str) of the platform or the embedded
            platform dict information.
    """
    if isinstance(platform_data, str):
        src_data: dict[dict, str] = src_api(
            f"https://speedrun.com/api/v1/platforms/{platform_data}"
        )

        src_platform = SrcPlatformModel.model_validate(src_data)
    else:
        src_platform = SrcPlatformModel.model_validate(platform_data)

    with transaction.atomic():
        Platforms.objects.update_or_create(
            id=src_platform.id, defaults={"name": src_platform.name}
        )
