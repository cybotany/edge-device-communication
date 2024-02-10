def process_nfc_url(ntag213, nfc_url):
    url_without_scheme = nfc_url.split('://')[1] if '://' in nfc_url else nfc_url
    return url_without_scheme
