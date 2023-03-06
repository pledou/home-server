FROM nextcloud:stable-fpm

RUN set -ex; \
    \
    apt-get update; \
    apt-get install -y --no-install-recommends --fix-missing \
        ffmpeg \
        lua5.3 liblua5.3-0 liblua5.3-dev \
        libmagickcore-6.q16-6-extra \
        procps \
        smbclient \
        supervisor \
        nginx \
        imagemagick\
        ghostscript\
    ; \
    rm -rf /var/lib/apt/lists/*

RUN # cp /usr/include/lua5.3/lua.h /usr/include; \
    # ln -s /usr/include/lua5.3/ /usr/include/lua; \
    # cp /usr/lib/x86_64-linux-gnu/liblua5.3.a /usr/lib/liblua.a; \
    # cp /usr/lib/x86_64-linux-gnu/liblua5.3.so /usr/lib/liblua.so; \
    # pecl install lua-2.0.7 \
    cd ~ \
    git clone https://github.com/singlecomm/php-lua.git \
    cd php-lua \
    git checkout php8 \
    phpize && ./configure --with-lua-version=5.3 \
    make \
    # The destination path may change depending on your PHP version \
    # You can find your extension directory by using: \
    # php -i | grep extension_dir \
    sudo cp ./.libs/lua.so /usr/local/lib/php/extensions/no-debug-non-zts-20210902

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
    docker-php-ext-configure imap --with-kerberos --with-imap-ssl; \
    docker-php-ext-install \
        bz2 \
        imap \
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

RUN mkdir -p \
    /var/log/supervisord \
    /var/run/supervisord \
;

COPY supervisord.conf /

ENV NEXTCLOUD_UPDATE=1

# Autoriser les aperçus de PDF par ImageMagick
RUN sed -i 's/\(^ *<policy.*rights="\)\([^"]*\)\(".*PDF.*\/>\)/\1read|write\3/1' /etc/ImageMagick-6/policy.xml

CMD ["/usr/bin/supervisord", "-c", "/supervisord.conf"]