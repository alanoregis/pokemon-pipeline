from pathlib import Path
import subprocess
import sys
import time

from export_parquet import export_gold_to_parquet
from ingestion.pipeline_pokemon import run_pipeline as run_ingestion


def run_command(command_str: str, cwd=None):
    """Executa comandos do dbt como string limpa no shell e valida retorno."""
    result = subprocess.run(command_str, cwd=cwd, shell=True)
    if result.returncode != 0:
        print(f"\n[ERRO] Falha ao executar: {command_str}")
        sys.exit(result.returncode)


def main():
    tempo_inicio = time.time()
    raiz = Path(__file__).resolve().parent
    pasta_dbt = raiz / "pokemon_dbt"

    print("\n" + "=" * 65)
    print(">>> INICIANDO PIPELINE COMPLETO DE DADOS (MODERN DATA STACK)")
    print("=" * 65)

    # 1. Ingestao da PokeAPI -> DuckDB Bronze
    print("\n[1/5] ETAPA 1: Ingestao com dlt (PokeAPI -> DuckDB Bronze)...")
    run_ingestion()

    # 2. Carregamento de Seeds (Traducoes para Portugues)
    print("\n[2/5] ETAPA 2: Carregando Seeds dbt (Traducoes PT-BR)...")
    run_command("uv run dbt seed --profiles-dir .", cwd=pasta_dbt)

    # 3. Transformacao no dbt (Bronze -> Silver -> Gold)
    print("\n[3/5] ETAPA 3: Transformacao com dbt (Silver -> Gold)...")
    run_command("uv run dbt run --profiles-dir .", cwd=pasta_dbt)

    # 4. Testes de Qualidade no dbt
    print("\n[4/5] ETAPA 4: Executando Testes de Qualidade Automatizados...")
    run_command("uv run dbt test --profiles-dir .", cwd=pasta_dbt)

    # 5. Exportacao da Gold para Parquet
    print("\n[5/5] ETAPA 5: Exportando Camada Gold para Parquet (Power BI)...")
    export_gold_to_parquet()

    tempo_total = round(time.time() - tempo_inicio, 2)
    print("\n" + "=" * 65)
    print(f">>> PIPELINE FINALIZADO COM SUCESSO EM APENAS {tempo_total} SEGUNDOS!")
    print("=" * 65 + "\n")


if __name__ == "__main__":
    main()
