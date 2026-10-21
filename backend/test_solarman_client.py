import hashlib

from app.services.integrations.solarman_client import SolarmanClient


client = SolarmanClient(
    app_id="TEST_APP_ID",
    app_secret="TEST_APP_SECRET",
)

password_sha256 = hashlib.sha256(
    b"TEST_PASSWORD"
).hexdigest()

request_data = client.build_token_request(
    email="teste@example.com",
    password_sha256=password_sha256,
    org_id="123456",
)

print(
    "URL correta:",
    request_data["url"].endswith("/account/v1.0/token"),
)

print(
    "App ID correto:",
    request_data["params"]["appId"] == "TEST_APP_ID",
)

print(
    "Language correto:",
    request_data["params"]["language"] == "en",
)

print(
    "Email correto:",
    request_data["json"]["email"] == "teste@example.com",
)

print(
    "Password é SHA-256:",
    len(request_data["json"]["password"]) == 64
    and request_data["json"]["password"] == password_sha256,
)

print(
    "App Secret presente:",
    bool(request_data["json"]["appSecret"]),
)

print(
    "Org ID correto:",
    request_data["json"]["orgId"] == "123456",
)