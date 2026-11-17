from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging
import threading
import dlt
import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

# 1. Silencia warnings cosméticos de inferência de schema vazio do dlt
logging.getLogger("dlt").setLevel(logging.ERROR)

# 2. Storage local para garantir uma sessão isolada por thread (100% Thread-Safe)
_thread_local = threading.local()


def get_resilient_session(retries: int = 3, backoff_factor: float = 2.0) -> requests.Session:
    """Cria uma sessão HTTP com TCP Keep-Alive e Retry exponencial para erros temporários."""
    session = requests.Session()
    retry_strategy = Retry(
        total=retries,
        backoff_factor=backoff_factor,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
        raise_on_status=False
    )
    adapter = HTTPAdapter(max_retries=retry_strategy, pool_connections=10, pool_maxsize=10)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


def get_thread_session() -> requests.Session:
    """Retorna uma sessão exclusiva e isolada para a thread em execução."""
    if not hasattr(_thread_local, "session"):
        _thread_local.session = get_resilient_session()
    return _thread_local.session


def fetch_single_pokemon(item: dict) -> dict:
    """Busca diretamente os detalhes essenciais do Pokémon (altura, peso, tipos, stats, sprites)."""
    session = get_thread_session()
    detail_res = session.get(item["url"], timeout=10)
    detail_res.raise_for_status()
    return detail_res.json()


@dlt.resource(name="raw_pokemon", write_disposition="replace")
def get_pokemon_data(limit: int = 151, max_workers: int = 4):
    """
    Recurso dlt com:
    - Extração otimizada em 1 chamada por Pokémon (151 no total).
    - Carga atômica 'Tudo ou Nada' (coleta em memória antes de entregar ao dlt).
    """
    main_session = get_thread_session()

    base_url = f"https://pokeapi.co/api/v2/pokemon?limit={limit}"
    response = main_session.get(base_url, timeout=10)
    response.raise_for_status()

    payload = response.json()
    pokemon_list = payload.get("results", [])

    # Contrato dinâmico: respeita o teto real retornado pela API
    expected_count = min(limit, payload.get("count", limit))
    if len(pokemon_list) < expected_count:
        raise ValueError(
            f"❌ Erro de Contrato: Esperados {expected_count} Pokémon, mas a API retornou {len(pokemon_list)}."
        )

    # 1. Coleta todas as respostas em memória primeiro (Atomicidade Tudo ou Nada)
    pokemon_data_list = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        try:
            futures = [
                executor.submit(fetch_single_pokemon, item)
                for item in pokemon_list
            ]
            for future in as_completed(futures):
                pokemon_data_list.append(future.result())
        except Exception:
            executor.shutdown(wait=True, cancel_futures=True)
            raise

    # 2. Entrega os dados validados e completos ao dlt
    yield from pokemon_data_list


def run_pipeline():
    ROOT_DIR = Path(__file__).resolve().parent.parent
    DATA_DIR = ROOT_DIR / "data"
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    db_path = str(DATA_DIR / "pokemon.duckdb")

    pipeline = dlt.pipeline(
        pipeline_name="pokemon_ingestion",
        destination=dlt.destinations.duckdb(db_path),
        dataset_name="bronze",
    )

    print("🚀 Ingerindo 151 Pokémon (chamadas otimizadas sem endpoint de espécies)...")
    load_info = pipeline.run(get_pokemon_data())
    print("✅ Ingestão concluída com sucesso na camada Bronze!")
    print(load_info)


if __name__ == "__main__":
    run_pipeline()
