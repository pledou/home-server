#!/bin/sh
# Stop all running indexes
php /var/www/html/occ fulltextsearch:stop
# Start live index
php /var/www/html/occ fulltextsearch:live

# More information: https://github.com/nextcloud/fulltextsearch/wiki/Commands