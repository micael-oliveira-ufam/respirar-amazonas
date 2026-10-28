"""CORS de leitura nos endpoints /publico/* (a página pública pode ficar no GitHub Pages)."""


def test_get_publico_tem_cors(client):
    for caminho in ("/publico/versao", "/publico/app", "/publico/painel?dias=30"):
        r = client.get(caminho, headers={"Origin": "https://exemplo.github.io"})
        assert r.headers.get("access-control-allow-origin") == "*", caminho


def test_preflight_publico_responde_204_sem_executar_a_rota(client):
    r = client.options("/publico/painel", headers={
        "Origin": "https://exemplo.github.io", "Access-Control-Request-Method": "GET",
        "Access-Control-Request-Headers": "cache-control,pragma"})
    assert r.status_code == 204
    assert r.headers["access-control-allow-origin"] == "*"
    assert r.headers["access-control-allow-methods"] == "GET, HEAD, OPTIONS"
    assert r.headers["access-control-allow-headers"] == "cache-control,pragma"


def test_fora_de_publico_nao_ganha_cors(client):
    r = client.get("/health", headers={"Origin": "https://exemplo.github.io"})
    assert "access-control-allow-origin" not in r.headers
    r = client.options("/respostas", headers={"Origin": "https://exemplo.github.io", "Access-Control-Request-Method": "POST"})
    assert "access-control-allow-origin" not in r.headers
