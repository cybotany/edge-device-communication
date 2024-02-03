def process_nfc_url(ntag213, nfc_url):
    if ntag213.debug:
        stripped_url = nfc_url.replace('http://', '')
    else:
        stripped_url = nfc_url.replace('https://', '')
    return stripped_url
