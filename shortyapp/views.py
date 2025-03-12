from django.shortcuts import render, redirect
from .models import ShortURL, ClickAnalytics
from django.utils import timezone
from django.shortcuts import get_object_or_404
from datetime import datetime
from django.urls import reverse
import random
import string
from celery import shared_task
from django.core.serializers.json import DjangoJSONEncoder
import redis
import json

redis_client = redis.StrictRedis(host='redis', port=6379, db=0)

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
        
        short_url = ShortURL(original_url=original_url, expiration_date=expiration_date, created_at=timezone.now())

        if custom_code:
            short_url.short_code = custom_code
        
        short_url.save()
        short_code = short_url.short_code
        short_url_full = request.build_absolute_uri(reverse('redirect', args=[short_url.short_code]))
        cache_short_url(short_url)
        
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

def cache_short_url(short_url):
    short_url_data = {
        'id': short_url.id,
        'original_url': short_url.original_url,
        'expiration_date': short_url.expiration_date.isoformat() if short_url.expiration_date else None,
    }
    redis_client.set(f'short_url:{short_url.short_code}', json.dumps(short_url_data, cls=DjangoJSONEncoder))
    redis_client.set(f'click_count:{short_url.short_code}', short_url.click_count)

def redirect_to_original(request, short_code):
    cached_url = redis_client.get(f'short_url:{short_code}')
    
    if cached_url:
        short_url_data = json.loads(cached_url.decode('utf-8'))
        
        if short_url_data['expiration_date']:
            expiration_date = datetime.fromisoformat(short_url_data['expiration_date'])
          
            if expiration_date < timezone.now():
                return render(request, 'expired.html')
        
        track_click.delay(short_url_data['id'], short_code)
        return redirect(short_url_data['original_url'])
    
    #queries the db if not found in the redis cache
    short_url = get_object_or_404(ShortURL, short_code=short_code)
    print(short_url.expiration_date)
    
    if short_url.expiration_date and short_url.expiration_date < timezone.now():
        return render(request, 'expired.html')
    

    cache_short_url(short_url)
    track_click.delay(short_url.id, short_code)
    
    return redirect(short_url.original_url)

@shared_task
def track_click(short_url_id, short_code):
    short_url = ShortURL.objects.get(id=short_url_id)
    ClickAnalytics.objects.create(
        short_url=short_url,
        timestamp=timezone.now()
    )
    short_url.click_count += 1
    short_url.save(update_fields=['click_count'])
    
    redis_client.set(f'click_count:{short_code}', short_url.click_count)

def click_analytics(request, short_code):
    short_url = get_object_or_404(ShortURL, short_code=short_code)

    cached_count = redis_client.get(f'click_count:{short_code}')
    if cached_count:
        click_count = int(cached_count.decode('utf-8'))
    else:
        click_count = short_url.click_count
      
        redis_client.set(f'click_count:{short_code}', click_count)
  
    click_analytics_entries = ClickAnalytics.objects.filter(short_url=short_url).order_by('-timestamp')
    
    short_url_full = request.build_absolute_uri(reverse('redirect', args=[short_code]))
    
    context = {
        'click_analytics_entries': click_analytics_entries,
        'short_url_full': short_url_full,
        'click_count': click_count,
        'expiration_date': short_url.expiration_date,
    }
    
    return render(request, 'click_analytics.html', context)
