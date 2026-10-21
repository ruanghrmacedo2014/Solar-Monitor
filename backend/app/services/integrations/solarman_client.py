import requests

class SolarmanIntegrationError(Exception):
    """Erro relacionado à comunicação com a API da Solarman."""

class SolarmanClient:
    def __init__(
        self,
        app_id: str,
        app_secret: str,
        base_url: str = "https://globalapi.solarmanpv.com",
    ):
        self.app_id = app_id
        self.app_secret = app_secret
        self.base_url = base_url.rstrip("/")

    def build_token_request(
        self,
        email: str,
        password_sha256: str,
        org_id: str | None = None,
        language: str = "en",
    ) -> dict:
        payload = {
            "email": email,
            "password": password_sha256,
            "appSecret": self.app_secret,
        }

        if org_id:
            payload["orgId"] = org_id

        return {
            "url": f"{self.base_url}/account/v1.0/token",
            "params": {
                "appId": self.app_id,
                "language": language,
            },
            "json": payload,
        }

    def authenticate(
        self,
        email: str,
        password_sha256: str,
        org_id: str | None = None,
        language: str = "en",
    ) -> dict:
        request_data = self.build_token_request(
            email=email,
            password_sha256=password_sha256,
            org_id=org_id,
            language=language,
        )

        try:
            response = requests.post(
                request_data["url"],
                params=request_data["params"],
                json=request_data["json"],
                timeout=30,
            )

            response.raise_for_status()

        except requests.RequestException as exc:
            raise SolarmanIntegrationError(
                "Não foi possível conectar à API da Solarman."
            ) from exc

        try:
            data = response.json()

        except ValueError as exc:
            raise SolarmanIntegrationError(
                "A API da Solarman retornou uma resposta inválida."
            ) from exc

        if data.get("success") is False:
            code = data.get("code")

            message = (
                data.get("msg")
                or data.get("message")
                or "A Solarman recusou a autenticação."
            )

            request_id = data.get("requestId")

            if code:
                raise SolarmanIntegrationError(
                    f"Erro da API da Solarman ({code}): {message} "
                    f"[requestId={request_id}]"
                )

            raise SolarmanIntegrationError(
                f"Erro da API da Solarman: {message} "
                f"[requestId={request_id}]"
            )

        return data

    def build_account_info_request(
        self,
        access_token: str,
        language: str = "en",
    ) -> dict:
        return {
            "url": f"{self.base_url}/account/v1.0/info",
            "params": {
                "appId": self.app_id,
                "language": language,
            },
            "headers": {
                "Authorization": f"Bearer {access_token}",
            },
        }

    def get_account_info(
        self,
        access_token: str,
        language: str = "en",
    ) -> dict:
        request_data = self.build_account_info_request(
            access_token=access_token,
            language=language,
        )

        try:
            response = requests.post(
                request_data["url"],
                params=request_data["params"],
                headers=request_data["headers"],
                json={},
                timeout=30,
            )

            response.raise_for_status()

        except requests.RequestException as exc:
            raise SolarmanIntegrationError(
                "Não foi possível consultar as informações da conta Solarman."
            ) from exc

        try:
            data = response.json()

        except ValueError as exc:
            raise SolarmanIntegrationError(
                "A API da Solarman retornou uma resposta inválida."
            ) from exc

        if data.get("success") is False:
            message = (
                data.get("msg")
                or data.get("message")
                or "A Solarman recusou a consulta."
            )

            code = data.get("code")
            request_id = data.get("requestId")

            if code:
                raise SolarmanIntegrationError(
                    f"Erro da API da Solarman ({code}): {message} "
                    f"[requestId={request_id}]"
                )

            raise SolarmanIntegrationError(
                f"Erro da API da Solarman: {message} "
                f"[requestId={request_id}]"
            )

        return data

    def build_station_base_request(
        self,
        access_token: str,
        station_id: int,
        company_id: int | None = None,
        user_id: int | None = None,
        language: str = "en",
    ) -> dict:
        payload = {
            "stationId": station_id,
        }

        if company_id is not None:
            payload["companyId"] = company_id

        if user_id is not None:
            payload["userId"] = user_id

        return {
            "url": f"{self.base_url}/station/v1.0/base",
            "params": {
                "language": language,
            },
            "headers": {
                "Authorization": access_token,
            },
            "json": payload,
        }

    def build_station_devices_request(
        self,
        access_token: str,
        station_id: int,
        page: int = 1,
        size: int = 50,
        device_type: str | None = None,
        language: str = "en",
    ) -> dict:
        payload = {
            "stationId": station_id,
            "page": page,
            "size": size,
        }

        if device_type is not None:
            payload["deviceType"] = device_type

        return {
            "url": f"{self.base_url}/station/v1.0/device",
            "params": {
                "language": language,
            },
            "headers": {
                "Authorization": access_token,
            },
            "json": payload,
        }

    def get_station_devices(
        self,
        access_token: str,
        station_id: int,
        page: int = 1,
        size: int = 50,
        device_type: str | None = None,
        language: str = "en",
    ) -> dict:
        request_data = self.build_station_devices_request(
            access_token=access_token,
            station_id=station_id,
            page=page,
            size=size,
            device_type=device_type,
            language=language,
        )

        try:
            response = requests.post(
                request_data["url"],
                params=request_data["params"],
                headers=request_data["headers"],
                json=request_data["json"],
                timeout=30,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            raise SolarmanIntegrationError(
                "Não foi possível consultar os devices da station Solarman."
            ) from exc

        try:
            data = response.json()
        except ValueError as exc:
            raise SolarmanIntegrationError(
                "A API da Solarman retornou uma resposta inválida."
            ) from exc

        if data.get("success") is False:
            message = (
                data.get("msg")
                or data.get("message")
                or "A Solarman recusou a consulta dos devices da station."
            )
            code = data.get("code")
            request_id = data.get("requestId")

            if code:
                raise SolarmanIntegrationError(
                    f"Erro da API da Solarman ({code}): {message} "
                    f"[requestId={request_id}]"
                )

            raise SolarmanIntegrationError(
                f"Erro da API da Solarman: {message} "
                f"[requestId={request_id}]"
            )

        return data

    def get_station_base(
        self,
        access_token: str,
        station_id: int,
        company_id: int | None = None,
        user_id: int | None = None,
        language: str = "en",
    ) -> dict:
        request_data = self.build_station_base_request(
            access_token=access_token,
            station_id=station_id,
            company_id=company_id,
            user_id=user_id,
            language=language,
        )

        try:
            response = requests.post(
                request_data["url"],
                params=request_data["params"],
                headers=request_data["headers"],
                json=request_data["json"],
                timeout=30,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            raise SolarmanIntegrationError(
                "Não foi possível consultar os dados básicos da station Solarman."
            ) from exc

        try:
            data = response.json()
        except ValueError as exc:
            raise SolarmanIntegrationError(
                "A API da Solarman retornou uma resposta inválida."
            ) from exc

        if data.get("success") is False:
            message = (
                data.get("msg")
                or data.get("message")
                or "A Solarman recusou a consulta da station."
            )
            code = data.get("code")
            request_id = data.get("requestId")

            if code:
                raise SolarmanIntegrationError(
                    f"Erro da API da Solarman ({code}): {message} "
                    f"[requestId={request_id}]"
                )

            raise SolarmanIntegrationError(
                f"Erro da API da Solarman: {message} "
                f"[requestId={request_id}]"
            )

        return data

    def build_station_list_request(
        self,
        access_token: str,
        page: int = 1,
        size: int = 50,
        language: str = "en",
    ) -> dict:
        payload = {
            "page": page,
            "size": size,
        }

        return {
            "url": f"{self.base_url}/station/v1.0/list",
            "params": {
                "language": language,
            },
            "headers": {
                "Authorization": access_token,
            },
            "json": payload,
        }

    def get_station_list(
        self,
        access_token: str,
        page: int = 1,
        size: int = 50,
        language: str = "en",
    ) -> dict:
        request_data = self.build_station_list_request(
            access_token=access_token,
            page=page,
            size=size,
            language=language,
        )

        try:
            response = requests.post(
                request_data["url"],
                params=request_data["params"],
                headers=request_data["headers"],
                json=request_data["json"],
                timeout=30,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            raise SolarmanIntegrationError(
                "Não foi possível consultar a lista de stations da Solarman."
            ) from exc

        try:
            data = response.json()
        except ValueError as exc:
            raise SolarmanIntegrationError(
                "A Solarman retornou uma resposta inválida."
            ) from exc

        if data.get("success") is False:
            message = (
                data.get("msg")
                or data.get("message")
                or "A Solarman recusou a consulta da lista de stations."
            )
            code = data.get("code")
            request_id = data.get("requestId")

            if code:
                raise SolarmanIntegrationError(
                    f"Erro da API da Solarman ({code}): {message} "
                    f"[requestId={request_id}]"
                )

            raise SolarmanIntegrationError(
                f"Erro da API da Solarman: {message} "
                f"[requestId={request_id}]"
            )

        return data

    def build_station_history_request(
        self,
        access_token: str,
        station_id: int,
        start_time: str,
        end_time: str,
        time_type: int = 2,
        language: str = "en",
    ) -> dict:
        payload = {
            "stationId": station_id,
            "timeType": time_type,
            "startTime": start_time,
            "endTime": end_time,
        }

        return {
            "url": f"{self.base_url}/station/v1.0/history",
            "params": {
                "language": language,
            },
            "headers": {
                "Authorization": access_token,
            },
            "json": payload,
        }

    def get_station_history(
        self,
        access_token: str,
        station_id: int,
        start_time: str,
        end_time: str,
        time_type: int = 2,
        language: str = "en",
    ) -> dict:
        request_data = self.build_station_history_request(
            access_token=access_token,
            station_id=station_id,
            start_time=start_time,
            end_time=end_time,
            time_type=time_type,
            language=language,
        )

        try:
            response = requests.post(
                request_data["url"],
                params=request_data["params"],
                headers=request_data["headers"],
                json=request_data["json"],
                timeout=30,
            )
        except requests.RequestException as exc:
            raise SolarmanIntegrationError(
                f"Erro ao consultar histórico da estação: {exc}"
            ) from exc

        try:
            data = response.json()
        except ValueError as exc:
            raise SolarmanIntegrationError(
                "SolarMan retornou uma resposta que não é JSON."
            ) from exc

        if not data.get("success"):
            raise SolarmanIntegrationError(
                data.get("msg")
                or "SolarMan retornou erro ao consultar histórico da estação."
            )

        return data