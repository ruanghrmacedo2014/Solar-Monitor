from app.services.integrations.solarman_client import SolarmanClient


client = SolarmanClient(
    app_id="TEST_APP_ID",
    app_secret="TEST_APP_SECRET",
)

request_data = client.build_account_info_request(
    access_token="TEST_ACCESS_TOKEN",
)

print(
    "URL correta:",
    request_data["url"].endswith("/account/v1.0/info"),
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
    "Authorization correto:",
    request_data["headers"]["Authorization"]
    == "Bearer TEST_ACCESS_TOKEN",
)