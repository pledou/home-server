FROM "{{ nextcloud_image }}:{{ nextcloud_version | default('stable') }}-fpm" AS nc_nextcloud

RUN set -ex; \
    \
    apt-get update; \
    apt-get install -y --no-install-recommends --fix-missing \
        ffmpeg \
        procps \
        supervisor \
        nginx \
        imagemagick \
        ghostscript \
        tesseract-ocr \ 
        tesseract-ocr-eng \ 
        tesseract-ocr-fra \
        smbclient \
    ; \
    rm -rf /var/lib/apt/lists/*


RUN set -ex; \
    \
    savedAptMark="$(apt-mark showmanual)"; \
    \
    apt-get update; \
    apt-get install -y --no-install-recommends \
        libbz2-dev \
        libkrb5-dev \
        libsmbclient-dev \
    ; \
    \
#    docker-php-ext-configure imap --with-kerberos --with-imap-ssl; \
    docker-php-ext-install \
        bz2 \
#        imap \
    ; \
    pecl install smbclient; \
    docker-php-ext-enable smbclient; \
    \
# reset apt-mark's "manual" list so that "purge --auto-remove" will remove all build dependencies
    apt-mark auto '.*' > /dev/null; \
    apt-mark manual $savedAptMark; \
    ldd "$(php -r 'echo ini_get("extension_dir");')"/*.so \
        | awk '/=>/ { print $3 }' \
        | sort -u \
        | xargs -r dpkg-query -S \
        | cut -d: -f1 \
        | sort -u \
        | xargs -rt apt-mark manual; \
    \
    apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false; \
    rm -rf /var/lib/apt/lists/*

# php-fpm configuration tuned for sustained load
# IMPORTANT: zzz-docker.conf (with 3 z's) loads AFTER www.conf (alphabetical order)
# This ensures our settings override defaults instead of being overridden.
RUN echo 'pm.max_children = {{ nextcloud_php_fpm_pm_max_children }}' >> /usr/local/etc/php-fpm.d/zzz-docker.conf && \
    echo 'pm.start_servers = {{ nextcloud_php_fpm_pm_start_servers }}' >> /usr/local/etc/php-fpm.d/zzz-docker.conf && \
    echo 'pm.min_spare_servers = {{ nextcloud_php_fpm_pm_min_spare_servers }}' >> /usr/local/etc/php-fpm.d/zzz-docker.conf && \
    echo 'pm.max_spare_servers = {{ nextcloud_php_fpm_pm_max_spare_servers }}' >> /usr/local/etc/php-fpm.d/zzz-docker.conf && \
    echo 'pm.max_requests = {{ nextcloud_php_fpm_pm_max_requests }}' >> /usr/local/etc/php-fpm.d/zzz-docker.conf && \
    echo 'request_terminate_timeout = {{ nextcloud_php_fpm_request_terminate_timeout }}' >> /usr/local/etc/php-fpm.d/zzz-docker.conf && \
    echo 'slowlog = /var/log/php-fpm-slow.log' >> /usr/local/etc/php-fpm.d/zzz-docker.conf && \
    echo 'request_slowlog_timeout = 60s' >> /usr/local/etc/php-fpm.d/zzz-docker.conf && \
    echo 'request_slowlog_trace_depth = 20' >> /usr/local/etc/php-fpm.d/zzz-docker.conf

# Keep preview generation enabled, but avoid overlap and cap runtime.
RUN echo '{{ nextcloud_preview_pregenerate_cron }}' >> /var/spool/cron/crontabs/www-data

RUN mkdir -p \
    /var/log/supervisord \
    /var/run/supervisord \
;

COPY supervisord.conf /
COPY fulltextsearch.sh /

ENV NEXTCLOUD_UPDATE=1

# Autoriser les aperçus de PDF par ImageMagick
# growing cache
RUN sed -i 's/\(^ *<policy.*rights="\)\([^"]*\)\(".*PDF.*\/>\)/\1read|write\3/1' /etc/ImageMagick-6/policy.xml; \
    sed -i 's/\(opcache\.memory_consumption=\).*/\1256/1' "${PHP_INI_DIR}/conf.d/opcache-recommended.ini"; \
    sed -i 's/\(opcache\.jit_buffer_size=\).*/\1256M/1' "${PHP_INI_DIR}/conf.d/opcache-recommended.ini"; \
    sed -i 's/\(memory_limit=\).*/\11024M/1' "${PHP_INI_DIR}/conf.d/nextcloud.ini";

CMD ["/usr/bin/supervisord", "-c", "/supervisord.conf"]