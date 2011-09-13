from pylons import config

import urllib
import urllib2

def check_recaptcha(request):
    '''Check a user's recaptcha submission is valid, and raise CaptchaError on failure.'''
    recaptcha_private_key = config.get('ckan.recaptcha.privatekey', '')
    if not recaptcha_private_key:
        # Recaptcha not enabled
        return
    
    client_ip_address = request.environ.get('REMOTE_ADDR', 'Unknown IP Address')
    recaptcha_challenge_field = request.params.get('recaptcha_challenge_field')
    recaptcha_response_field = request.params.get('recaptcha_response_field')

    recaptcha_server_name = 'http://api-verify.recaptcha.net/verify'

    params = urllib.urlencode(dict(privatekey=recaptcha_private_key,
                                   remoteip=client_ip_address,
                                   challenge=recaptcha_challenge_field,
                                   response=recaptcha_response_field))
    f = urllib2.urlopen(recaptcha_server_name, params)
    data = f.read()
    f.close()
    if not data.lower().startswith('true'):
        raise CaptchaError()

class CaptchaError(ValueError):
    pass

