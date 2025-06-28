from django.db import migrations


def remove_duplicate_categories(apps, schema_editor):
    Category = apps.get_model('transactions', 'Category')

    users_with_categories = Category.objects.values_list(
        'user', flat=True).distinct()

    for user_id in users_with_categories:
        user_categories = Category.objects.filter(user_id=user_id)

        unique_names = user_categories.values_list(
            'name', flat=True).distinct()

        for name in unique_names:
            duplicates = Category.objects.filter(user_id=user_id, name=name)

            if duplicates.count() > 1:
                keeper = duplicates.first()

                duplicates.exclude(pk=keeper.pk).delete()


class Migration(migrations.Migration):
    dependencies = [
        # Укажите последнюю миграцию вашего приложения
        # Замените xxxx на номер последней миграции
        ('transactions', '0003_alter_category_options_alter_transaction_options_and_more'),
    ]

    operations = [
        migrations.RunPython(remove_duplicate_categories),
    ]
