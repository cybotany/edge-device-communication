def process_ntag_url(ntag, ntag_url):
    url_without_scheme = ntag_url.split('://')[1] if '://' in ntag_url else ntag_url
    return url_without_scheme
