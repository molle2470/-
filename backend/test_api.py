"""신규 상품 uvicorn 테스트"""
import json
import urllib.request

BASE = "http://localhost:28081/api/v1"


def test_product(product_id):
    url = BASE + "/extension/products"
    data = json.dumps({
        "source": "musinsa",
        "product": {
            "name": "test",
            "original_price": 50000,
            "source_url": f"https://www.musinsa.com/products/{product_id}",
            "source_product_id": str(product_id),
            "brand_name": "testbrand",
        },
    }).encode("utf-8")
    req = urllib.request.Request(
        url, data=data, method="POST",
        headers={"Content-Type": "application/json", "X-Extension-Key": "sourcing-extension-phase1-key"},
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, resp.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()


print("=== uvicorn 28081 테스트 ===")
for pid in ["4371041", "2020202"]:
    status, body = test_product(pid)
    print(f"  {pid} → {status}: {body}")
