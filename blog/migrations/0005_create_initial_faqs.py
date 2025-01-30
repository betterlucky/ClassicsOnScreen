from django.db import migrations

def create_initial_faqs(apps, schema_editor):
    FAQ = apps.get_model('blog', 'FAQ')
    
    initial_faqs = [
        # General Questions
        {
            'category': 'general',
            'question': 'What is Classics On Screen?',
            'answer': 'Classics On Screen is a platform dedicated to bringing classic films back to the big screen. Take a look at our <a href="/about/">About</a> page for more information.',
            'order': 1
        },
        # ... rest of the FAQs ...
    ]
    
    for faq_data in initial_faqs:
        FAQ.objects.create(**faq_data)

def remove_initial_faqs(apps, schema_editor):
    FAQ = apps.get_model('blog', 'FAQ')
    FAQ.objects.all().delete()

class Migration(migrations.Migration):
    dependencies = [
        ('blog', '0004_create_faq_model'),
    ]

    operations = [
        migrations.RunPython(create_initial_faqs, remove_initial_faqs),
    ] 