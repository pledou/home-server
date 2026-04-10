# strongSwan 5.9.14 with eap-radius plugin (compiled from source)
# Based on the exact same build as strongx509/strongswan:5.9.14, adding:
#   --enable-eap-radius   (RADIUS authentication backend)
#   --enable-fips-prf     (required for EAP-MSCHAPv2)
#   --enable-pkcs8        (private key loading)
#   --enable-pkcs12       (certificate bundle loading)

FROM ubuntu:22.04

ENV VERSION=5.9.14
ENV DEBIAN_FRONTEND=noninteractive

RUN DEV_PACKAGES="wget bzip2 build-essential libssl-dev libgmp-dev" && \
    apt-get -y update && \
    apt-get -y install --no-install-recommends ca-certificates iproute2 iputils-ping $DEV_PACKAGES && \
    mkdir /strongswan-build && \
    cd /strongswan-build && \
    wget https://download.strongswan.org/strongswan-${VERSION}.tar.bz2 && \
    tar xfj strongswan-${VERSION}.tar.bz2 && \
    cd strongswan-${VERSION} && \
    ./configure \
        --prefix=/usr \
        --sysconfdir=/etc \
        --disable-defaults \
        --enable-charon \
        --enable-ikev2 \
        --enable-nonce \
        --enable-random \
        --enable-openssl \
        --enable-pem \
        --enable-x509 \
        --enable-pubkey \
        --enable-constraints \
        --enable-pki \
        --enable-socket-default \
        --enable-kernel-netlink \
        --enable-swanctl \
        --enable-resolve \
        --enable-eap-identity \
        --enable-eap-md5 \
        --enable-eap-dynamic \
        --enable-eap-tls \
        --enable-eap-radius \
        --enable-fips-prf \
        --enable-pkcs1 \
        --enable-pkcs8 \
        --enable-pkcs12 \
        --enable-pgp \
        --enable-dnskey \
        --enable-sshkey \
        --enable-updown \
        --enable-vici \
        --enable-counters \
        --enable-silent-rules && \
    make all && \
    make install && \
    cd / && rm -rf /strongswan-build && \
    ln -s /usr/libexec/ipsec/charon /usr/local/bin/charon && \
    apt-get -y remove $DEV_PACKAGES && \
    apt-get -y autoremove && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

EXPOSE 500/udp 4500/udp

COPY strongswan-startup.sh /usr/local/bin/strongswan-startup.sh
RUN chmod +x /usr/local/bin/strongswan-startup.sh

CMD ["/usr/local/bin/strongswan-startup.sh"]
