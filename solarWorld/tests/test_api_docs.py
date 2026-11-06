def test_openapi_schema_is_available(client):
    response = client.get("/api/schema/?format=json")

    assert response.status_code == 200
    schema = response.json()
    assert schema["info"]["title"] == "Solar World API"
    assert "/api/planets/" in schema["paths"]


def test_swagger_ui_is_available(client):
    response = client.get("/api/docs/")

    assert response.status_code == 200
    assert b"swagger-ui" in response.content.lower()
