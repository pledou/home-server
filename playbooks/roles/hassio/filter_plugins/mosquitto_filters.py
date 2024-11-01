from ansible.errors import AnsibleError
from passlib.hash import pbkdf2_sha512


def mosquitto_passwd(passwd):
    SALT_SIZE = 12
    ITERATIONS = 101
    
    digest = pbkdf2_sha512.using(salt_size=SALT_SIZE, rounds=ITERATIONS)\
                                        .hash(passwd) \
                                        .replace('pbkdf2-sha512', '7') \
                                        .replace('.', '+')

    return digest + '=='


class FilterModule(object):
    def filters(self):
        return {
            'mosquitto_passwd': mosquitto_passwd,
        }