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

{% if gpu == 'intel' %}
RUN apt-get update && \
    apt-get install -y lsb-release && \
    echo "deb http://ftp.debian.org/debian $(lsb_release -cs) non-free" >> \
       /etc/apt/sources.list.d/intel-graphics.list && \
    apt-get update && \
    apt-get install -y intel-media-va-driver-non-free ffmpeg && \
    rm -rf /var/lib/apt/lists/*

RUN GID=`stat -c "%g" /dev/dri/renderD128` && \
    groupadd -g $GID render2 || true && \
    GROUP=`getent group $GID | cut -d: -f1` && \
    usermod -aG $GROUP www-data
# CF https://memories.gallery/hw-transcoding/#docker

RUN set -ex; \
    apt-get update; \
    apt-get install -y --no-install-recommends \
        python3 \
        python3-pip \
        python3-venv \
        intel-opencl-icd \
        intel-level-zero-gpu \
        level-zero \
    ; \
    rm -rf /var/lib/apt/lists/*

RUN pip3 install --no-cache-dir \
        pillow \
        numpy \
        opencv-python-headless \
        onnxruntime \
        onnx \
        tensorflow==2.15.0 \
        intel-extension-for-tensorflow==2.15.0 \
        openvino==2024.4.0 \
        openvino-dev==2024.4.0

RUN apt-get update && \
    apt-get install -y \
        intel-opencl-icd \
        intel-level-zero-gpu \
        level-zero \
    && rm -rf /var/lib/apt/lists/*

ENV TF_ENABLE_ONEDNN_OPTS=1
ENV TF_XPU_ONEDNN_ENABLE=1
ENV OPENVINO_DEVICE=GPU

{% endif %}

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