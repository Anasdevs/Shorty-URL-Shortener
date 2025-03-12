# Base image
FROM python:3.12-slim

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        nginx \
        sqlite3 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN python manage.py collectstatic --noinput

RUN echo "server {\n\
    listen 80;\n\
    server_name localhost;\n\
    location /static/ {\n\
        alias /app/static/;\n\
    }\n\
    location / {\n\
        proxy_pass http://127.0.0.1:8000;\n\
        proxy_set_header Host \$host;\n\
        proxy_set_header X-Real-IP \$remote_addr;\n\
    }\n\
}" > /etc/nginx/sites-available/default

RUN mkdir -p /app/staticfiles \
    && chown -R www-data:www-data /app/staticfiles \
    && chown -R www-data:www-data /app/db.sqlite3

EXPOSE 80

RUN echo "#!/bin/bash\n\
nginx &\n\
python manage.py runserver 0.0.0.0:8000\n\
" > /app/start.sh \
    && chmod +x /app/start.sh

CMD ["/app/start.sh"]
