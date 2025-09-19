



from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Item',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity', models.PositiveIntegerField()),
                ('total_price', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('inventory', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='products.inventory')),

            ],
        ),
        migrations.CreateModel(
            name='ShoppingCart',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now_add=True)),
                ('item', models.ManyToManyField(related_name='item', to='cart.item')),
                ('user', models.OneToOneField(limit_choices_to={'user_type': 'artisan'}, on_delete=django.db.models.deletion.CASCADE, to='users.user')),
            ],
        ),
    ]
