import requests
from src.allocation import config

def post_to_add_batch(ref, sku, qty, eta):
    url = config.get_api_url()
    r = requests.post(
        f'{url}/batches',
        json={'ref': ref, 'sku': sku, 'qty': qty, 'eta': eta}
    )
    
    assert r.status_code == 200

def post_to_allocate(orderid, sku, qty, expect_success=True):
    url = config.get_api_url()
    r = requests.post(
        f'{url}/allocate', 
        json={'orderid': orderid, 'sku': sku, 'qty': qty}
    )
    if expect_success:
        assert r.status_code == 200
    return r

def post_to_deallocate(orderid, sku, qty, expect_success=True):
    url = config.get_api_url()
    r = requests.post(
        f'{url}/deallocate', 
        json={'orderid': orderid, 'sku': sku, 'qty': qty}
    )
    if expect_success:
        assert r.status_code == 200
    return r

