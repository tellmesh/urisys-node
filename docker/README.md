# urisys-node Docker GUI — host control E2E

Slave z wirtualnym pulpitem (Xvfb + zenity) i `urisys-node serve` na porcie **8790**.
Obraz instaluje **`urisys`** (controller + `urisys-node` w jednym pakiecie), tak jak:

```bash
pip install urisys
urisys --help
urisys-node serve --port 8790
```

## Wymagania

- Docker + compose v2
- Monorepo **tellmesh** (build context obejmuje `urisys/`, `uricore/`, `urikvm-docker/`)

## Uruchomienie testu (host → kontener)

```bash
cd urisys
bash scripts/run-urisys-node-docker-e2e.sh
```

Test sprawdza:

1. `docker compose up` — Xvfb, okno zenity, `urisys-node serve :8790`
2. W kontenerze: `urisys --help`, `urisys-node serve --help`
3. Z hosta: `GET /health`, `GET /uri/routes`
4. Z hosta przez route-map: `urisys-node call node://docker-slave/query/identity`
5. Z hosta: `screen://…/command/capture` (mss na Xvfb, plik >500 B)
6. Z hosta: `node://local/command/indicator-on/off`
7. Z hosta: `GET /events`

## Ręczna kontrola

```bash
docker compose -f urisys-node/docker/docker-compose.gui.yml up -d --build
curl http://127.0.0.1:8790/health

urisys-node call screen://docker-slave/monitor/primary/command/capture \
  --route-map urisys-node/docker/config/route-map.host.yaml \
  --nodes-registry urisys-node/docker/config/nodes.registry.host.json \
  --approve --allow-real
```

## Pytest (opcjonalnie)

```bash
URISYS_NODE_DOCKER_E2E=1 pytest urisys-node/tests/test_docker_host_e2e.py -q
```

## Porty / env

| Zmienna | Domyślnie | Opis |
|---------|-----------|------|
| `URISYS_NODE_HOST_PORT` | 8790 | mapowanie host:container |
| `URISYS_NODE_E2E_KEEP` | 0 | `1` = nie `docker compose down` po teście |
