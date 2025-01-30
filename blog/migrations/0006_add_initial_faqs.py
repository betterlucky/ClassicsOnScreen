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
        {
            'category': 'general',
            'question': 'How do I find upcoming screenings?',
            'answer': 'You can find all our upcoming screenings on the <a href="/">Home</a> page. As people create new screenings, they\'ll appear there automatically.',
            'order': 2
        },
        {
            'category': 'general',
            'question': 'Why do new shows have to be at least 3 weeks in the future?',
            'answer': 'There are two main reasons for this: the first is that the venue has to plan their own programme and need to have time to work around your show if need be. The second is that, for cinemas at least, films are not available "on-demand" and booking new films tends to be manual, slow and time-consuming.',
            'order': 3
        },
        {
            'category': 'general',
            'question': 'Why do films get removed from the available films list?',
            'answer': '''Due to licensing agreements and costs, we can only maintain a limited number of films as active on our platform at any time. 
                To manage this, we use a voting system where:
                <ul>
                    <li>Each user can vote for up to 5 films at a time</li>
                    <li>Votes last for 30 days</li>
                    <li>Films with fewer votes may be rotated out to make room for new selections</li>
                    <li>You can see the most popular films and their vote counts at the top of our <a href="/films/">Films</a> page</li>
                </ul>
                This system helps us ensure we\'re maintaining licenses for the films our community most wants to see.''',
            'order': 4
        },
        # Tickets and Booking
        {
            'category': 'tickets',
            'question': 'How do I purchase tickets?',
            'answer': 'You can buy credits via your profile page and use these to buy tickets for a particular show or create one of your own!',
            'order': 1
        },
        {
            'category': 'tickets',
            'question': 'What is your refund policy?',
            'answer': 'Typically, we arrange for cinema tickets for regular shows (not including special events) at your local cinema rather than issuing refunds. However, feel free to reach out via the <a href="/contact/">Contact Us</a> page.',
            'order': 2
        },
        {
            'category': 'tickets',
            'question': 'Why credits?',
            'answer': 'Here\'s the thing, we want to keep things as simple as possible. Due to the costs involved, we also need to keep refunds and other cash transfers to a minimum. A credits system allows you to use your ticket anywhere without having to worry about having to top up the difference in ticket prices or have a stray 50p sitting in your account.',
            'order': 3
        },
        {
            'category': 'tickets',
            'question': 'I\'ve seen films at a particular cinema cheaper than the credits you have here. Why is that?',
            'answer': 'It\'s partly down us being able to handle multiple sites with different ticket prices, it\'s partly because we don\'t want to have to use booking fees and it\'s partly down to the fact that one-off shows cost more to put on (see our <a href="/about/">About</a> page for more on that last bit).',
            'order': 4
        },
        # Other Questions
        {
            'category': 'other',
            'question': 'How can I suggest a film?',
            'answer': 'You can suggest films through our <a href="/contact/">Contact Us</a> page. We appreciate your suggestions!',
            'order': 1
        },
        {
            'category': 'other',
            'question': 'Why is there a subtitles option?',
            'answer': 'When you create a show, you can request that it be subtitled. It may be that you or some of the other potential audience members have a hearing impediment, it may be that you\'re planning a sing-a-long and want the lyrics on screen or simply that you find that some of the dialogue in recent Hollywood films can be a little mumbled....',
            'order': 2
        },
        {
            'category': 'other',
            'question': 'Why is there a relaxed option?',
            'answer': '''There are times when watching a film with strict cinema rules can cause problems. There may be neurodiverse audience members that find it difficult to settle for the whole length of the film. Some people have back or leg issues that mean they really need to get up every 30 minutes for a bit of a wander or a stretch. Or, let's be honest, you may just be wanting a party screening.
                
                Marking your show as "relaxed" means that other audience members will be aware that not everyone is going to be sitting quietly. We'll also typically arrange for the lights to not go all the way down and the volume will not be quite as high as a regular show (unless it's a party night!).''',
            'order': 3
        },
    ]
    
    for faq_data in initial_faqs:
        FAQ.objects.create(**faq_data)

def remove_initial_faqs(apps, schema_editor):
    FAQ = apps.get_model('blog', 'FAQ')
    FAQ.objects.all().delete()

class Migration(migrations.Migration):
    dependencies = [
        ('blog', '0005_create_initial_faqs'),
    ]

    operations = [
        migrations.RunPython(create_initial_faqs, remove_initial_faqs),
    ] 