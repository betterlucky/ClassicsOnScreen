# Generated by Django 5.1.5 on 2025-01-28 21:26

import django.contrib.auth.models
import django.contrib.auth.validators
import django.core.validators
import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='Film',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('description', models.TextField(blank=True, null=True)),
                ('active', models.BooleanField(default=True)),
                ('overridecapacity', models.IntegerField(blank=True, null=True)),
                ('imdb_code', models.CharField(max_length=20, unique=True, validators=[django.core.validators.RegexValidator(message='IMDB code must be in the format "tt" followed by 7-8 digits (e.g., tt0111161)', regex='^tt\\d{7,8}$')])),
            ],
            options={
                'verbose_name': 'Film',
                'verbose_name_plural': 'Films',
            },
        ),
        migrations.CreateModel(
            name='Location',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=60, unique=True)),
                ('contact_email', models.EmailField(help_text='Direct contact email for the venue manager', max_length=254, verbose_name='Venue Manager Email')),
                ('min_capacity', models.IntegerField(default=40, help_text='Minimum number of credits required for show confirmation')),
                ('max_capacity', models.IntegerField(default=100, help_text='Maximum number of credits allowed for this venue')),
                ('active', models.BooleanField(default=True, help_text='Whether this venue is currently available for shows')),
            ],
            options={
                'verbose_name': 'Location',
                'verbose_name_plural': 'Locations',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='ShowOption',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, unique=True)),
                ('description', models.TextField(blank=True, help_text='Explain what this option means for the show')),
                ('active', models.BooleanField(default=True, help_text='Whether this option is currently available')),
            ],
            options={
                'verbose_name': 'Show Option',
                'verbose_name_plural': 'Show Options',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='VenueOwner',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True)),
                ('description', models.TextField(blank=True, null=True)),
                ('website', models.URLField(blank=True, null=True)),
                ('contact_email', models.EmailField(help_text='Primary contact email for the company', max_length=254, verbose_name='Head Office Email')),
            ],
            options={
                'verbose_name': 'Venue Owner',
                'verbose_name_plural': 'Venue Owners',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='SiteUser',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('username', models.CharField(error_messages={'unique': 'A user with that username already exists.'}, help_text='Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.', max_length=150, unique=True, validators=[django.contrib.auth.validators.UnicodeUsernameValidator()], verbose_name='username')),
                ('first_name', models.CharField(blank=True, max_length=150, verbose_name='first name')),
                ('last_name', models.CharField(blank=True, max_length=150, verbose_name='last name')),
                ('email', models.EmailField(blank=True, max_length=254, verbose_name='email address')),
                ('is_staff', models.BooleanField(default=False, help_text='Designates whether the user can log into this admin site.', verbose_name='staff status')),
                ('is_active', models.BooleanField(default=True, help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.', verbose_name='active')),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date joined')),
                ('credits', models.IntegerField(blank=True, default=0, null=True)),
                ('groups', models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.group', verbose_name='groups')),
                ('user_permissions', models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.permission', verbose_name='user permissions')),
            ],
            options={
                'verbose_name': 'user',
                'verbose_name_plural': 'users',
                'abstract': False,
            },
            managers=[
                ('objects', django.contrib.auth.models.UserManager()),
            ],
        ),
        migrations.CreateModel(
            name='Show',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('body', models.TextField(help_text='Description and details about the show')),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('last_modified', models.DateTimeField(auto_now=True)),
                ('eventtime', models.DateTimeField(help_text='Scheduled date and time of the show')),
                ('credits', models.PositiveIntegerField(blank=True, default=0, null=True)),
                ('status', models.CharField(choices=[('inactive', 'Inactive'), ('tbc', 'To Be Confirmed'), ('confirmed', 'Confirmed'), ('cancelled', 'Cancelled'), ('completed', 'Completed'), ('expired', 'Expired')], default='inactive', max_length=10)),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('film', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='shows', to='blog.film')),
                ('location', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='shows', to='blog.location')),
                ('options', models.ManyToManyField(blank=True, help_text='Special features for this show', related_name='shows', to='blog.showoption')),
            ],
            options={
                'verbose_name': 'Show',
                'verbose_name_plural': 'Shows',
                'ordering': ['eventtime'],
                'unique_together': {('film', 'location', 'eventtime')},
            },
        ),
        migrations.CreateModel(
            name='Comment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('body', models.TextField()),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('author', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('show', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='comments', to='blog.show')),
            ],
            options={
                'verbose_name': 'Comment',
                'verbose_name_plural': 'Comments',
                'ordering': ['-created_on'],
            },
        ),
        migrations.CreateModel(
            name='ShowCreditLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('credits', models.PositiveIntegerField()),
                ('refunded', models.BooleanField(default=False)),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('show', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='credit_logs', to='blog.show')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Show Credit Log',
                'verbose_name_plural': 'Show Credit Logs',
                'ordering': ['created_on'],
            },
        ),
        migrations.AddField(
            model_name='location',
            name='owner',
            field=models.ForeignKey(blank=True, help_text='The company or individual that owns this venue (optional for independent venues)', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='locations', to='blog.venueowner'),
        ),
    ]
