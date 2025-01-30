from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('blog', '0003_filmvote'),
    ]

    operations = [
        migrations.CreateModel(
            name='FAQ',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('question', models.CharField(max_length=255)),
                ('answer', models.TextField()),
                ('category', models.CharField(choices=[('general', 'General Questions'), ('tickets', 'Tickets and Booking'), ('other', 'Other Questions')], max_length=20)),
                ('order', models.IntegerField(default=0)),
                ('active', models.BooleanField(default=True)),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('updated_on', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'FAQ',
                'verbose_name_plural': 'FAQs',
                'ordering': ['category', 'order', 'created_on'],
            },
        ),
    ] 