FROM nginx:mainline

#SHELL ["/bin/bash", "-xo", "pipefail", "-c"]

# Install some deps, lessc and less-plugin-clean-css, and wkhtmltopdf
RUN apt-get update \
        && apt-get install -y --no-install-recommends \
            certbot \
            python3-certbot-nginx \
            && rm -rf /var/lib/apt/lists/*

# Mount
VOLUME ["/etc/nginx/sites-available", "/etc/nginx/sites-enabled", "/var/lib/letsencrypt", "/etc/letsencrypt"]

# Expose services
EXPOSE 80 443

CMD ["nginx", "-g", "daemon off;"]
