FROM nextcloud:stable-fpm AS nc_nextcloud

RUN set -ex; \
    \
    apt-get update; \
    apt-get install -y --no-install-recommends --fix-missing \
        ffmpeg \
        libmagickcore-6.q16-6-extra \
        procps \
#        smbclient \
        supervisor \
        nginx \
        imagemagick\
        ghostscript\
        git\
    ;
    #rm -rf /var/lib/apt/lists/*

# RUN cd ~; \
#     git clone https://github.com/singlecomm/php-lua.git; \
#     cd ./php-lua; \
#     git checkout php8; \
#     phpize && ./configure --with-lua-version=5.3; \
#     make; \
#     # The destination path may change depending on your PHP version \
#     # You can find your extension directory by using: \
#     # php -i | grep extension_dir \
#     cp ./.libs/lua.so /usr/local/lib/php/extensions/no-debug-non-zts-20210902/; \
#     docker-php-ext-enable lua;

RUN set -ex; \
    \
    savedAptMark="$(apt-mark showmanual)"; \
    \
    apt-get update; \
    apt-get install -y --no-install-recommends \
        libbz2-dev \
        libc-client-dev \
        libkrb5-dev \
        libsmbclient-dev \
    ; \
    \
#    docker-php-ext-configure imap --with-kerberos --with-imap-ssl; \
    docker-php-ext-install \
        bz2 \
#        imap \
    ; \
#    pecl install smbclient; \
#    docker-php-ext-enable smbclient; \
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

RUN mkdir -p \
    /var/log/supervisord \
    /var/run/supervisord \
;

COPY supervisord.conf /

ENV NEXTCLOUD_UPDATE=1

# Autoriser les aperçus de PDF par ImageMagick
RUN sed -i 's/\(^ *<policy.*rights="\)\([^"]*\)\(".*PDF.*\/>\)/\1read|write\3/1' /etc/ImageMagick-6/policy.xml

CMD ["/usr/bin/supervisord", "-c", "/supervisord.conf"]