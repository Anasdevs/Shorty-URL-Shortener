from django.shortcuts import render, redirect
from django.http import HttpResponse
from .models import ShortURL, ClickAnalytics
from django.utils import timezone
from django.shortcuts import get_object_or_404
from datetime import datetime
from django.urls import reverse
import random
import string

def index(request):
    if request.method == 'POST':
        original_url = request.POST['original_url']
        custom_code = request.POST['custom_code']
        expiration_date_str = request.POST.get('expiration_date', None)
        print(expiration_date_str)
        if not custom_code:
            custom_code = generate_random_short_code()
        
        if custom_code and ShortURL.objects.filter(short_code=custom_code).exists():
            return render(request, 'index.html', {'error_message': 'Custom short code already taken.'})
        
        expiration_date = None
        if expiration_date_str:
            expiration_date = timezone.make_aware(datetime.strptime(expiration_date_str, '%Y-%m-%dT%H:%M'), timezone.get_current_timezone())
        
        short_url = ShortURL(original_url=original_url, expiration_date=expiration_date)
        if custom_code:
            short_url.short_code = custom_code
        
        short_url.save()
        short_code = short_url.short_code
        short_url_full = request.build_absolute_uri(reverse('redirect', args=[short_url.short_code]))
        
        context = {
            'short_url_full': short_url_full,
            'short_code': short_code,
            'expiration_date': expiration_date,
        }

        return render(request, 'success.html', context)

    return render(request, 'index.html')

def generate_random_short_code(length=6):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

def redirect_to_original(request, short_code):
    short_url = get_object_or_404(ShortURL, short_code=short_code)
    print(short_url.expiration_date)
    
    if short_url.expiration_date and short_url.expiration_date < timezone.now():
        return render(request, 'expired.html')
    
    # Create a ClickAnalytics entry to track the click
    ClickAnalytics.objects.create(
        short_url=short_url,
        ip_address=request.META['REMOTE_ADDR'],
        timestamp=timezone.now()
    )
    short_url.click_count += 1
    short_url.save()
    
    return redirect(short_url.original_url)



def click_analytics(request, short_code):
    short_url = get_object_or_404(ShortURL, short_code=short_code)
    click_analytics_entries = ClickAnalytics.objects.filter(short_url=short_url)
    
    short_url_full = request.build_absolute_uri(reverse('redirect', args=[short_code]))
    click_count = short_url.click_count
    
    context = {
        'click_analytics_entries': click_analytics_entries,
        'short_url_full': short_url_full,
        'click_count': click_count,
        'expiration_date': short_url.expiration_date,
    }
    
    return render(request, 'click_analytics.html', context)
