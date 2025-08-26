from django.db import migrations


def extract_role_from_name(name):
    name_lower = name.lower()

    roles = ["admin", "moderator", "contributor", "read_only"]

    for role in roles:
        if role in name_lower:
            return role

    return "read_only"


def migrate_api_keys(apps, schema_editor):
    APIKey = apps.get_model("rest_framework_api_key", "APIKey")
    RoleAPIKey = apps.get_model("api", "RoleAPIKey")

    existing_keys = APIKey.objects.all()
    for api_key in existing_keys:
        try:
            role = extract_role_from_name(api_key.name)

            if RoleAPIKey.objects.filter(name=api_key.name).exists():
                continue

            role_api_key = RoleAPIKey(
                id=api_key.id,
                name=api_key.name,
                hashed_key=api_key.hashed_key,
                prefix=api_key.prefix,
                created=api_key.created,
                revoked=api_key.revoked,
                expiry_date=api_key.expiry_date,
                role=role,
                description=f"Migrated from old APIKey system. Extracted role: {role}",
                created_by="migration",
            )
            role_api_key.save()

        except Exception:
            continue


def reverse_migrate_api_keys(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0001_initial"),
        ("rest_framework_api_key", "0005_auto_20220110_1102"),  # Use existing migration
    ]

    operations = [
        migrations.RunPython(
            migrate_api_keys, reverse_migrate_api_keys, hints={"verbosity": 2}
        ),
    ]
