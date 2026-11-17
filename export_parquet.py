from pathlib import Path
import duckdb


def export_gold_to_parquet():
    # 1. Localiza a raiz do projeto e os arquivos na pasta data/
    root_dir = Path(__file__).resolve().parent
    db_path = root_dir / "data" / "pokemon.duckdb"
    output_parquet = root_dir / "data" / "pokemon_gold.parquet"

    if not db_path.exists():
        # Fallback caso o script seja executado de uma subpasta
        root_dir = Path(__file__).resolve().parent.parent
        db_path = root_dir / "data" / "pokemon.duckdb"
        output_parquet = root_dir / "data" / "pokemon_gold.parquet"

    print(f" Conectando ao DuckDB em: {db_path}")
    conn = duckdb.connect(str(db_path), read_only=True)

    print(f" Exportando a camada Gold para Parquet...")

    # 2. Executa a exportação colunar nativa de alta performance
    conn.execute(
        f"COPY gold.gold_pokemon TO '{output_parquet.as_posix()}' (FORMAT PARQUET);"
    )

    # 3. Valida se o arquivo gerado está íntegro
    total_rows = conn.execute(
        f"SELECT count(*) FROM read_parquet('{output_parquet.as_posix()}')"
    ).fetchone()[0]

    conn.close()

    print(f" Concluído! {total_rows} Pokémons exportados com sucesso.")
    print(f" Arquivo gerado em: {output_parquet}")
    print(" Agora basta abrir esse arquivo no Power BI!")


if __name__ == "__main__":
    export_gold_to_parquet()