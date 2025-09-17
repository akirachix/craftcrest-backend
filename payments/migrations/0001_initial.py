

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Payment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('transaction_code', models.CharField(max_length=50)),
                ('status', models.CharField(max_length=20)),
                ('paid_at', models.DateTimeField()),
                ('released_at', models.DateTimeField(blank=True, null=True)),
                ('held_by_platform', models.BooleanField(default=True)),
                ('artisan_id', models.ForeignKey(limit_choices_to={'user_type': 'artisan'}, on_delete=django.db.models.deletion.CASCADE, to='users.user')),
                ('order_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='orders.order')),

            ],
        ),
    ]
