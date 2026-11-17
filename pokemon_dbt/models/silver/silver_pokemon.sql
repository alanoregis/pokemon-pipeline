WITH base AS (
    SELECT 
        _dlt_id,
        id AS pokemon_id,
        UPPER(name) AS nome_pokemon,
        base_experience AS experiencia_base,
        CAST(height / 10.0 AS NUMERIC(6, 2)) AS altura_metros,
        CAST(weight / 10.0 AS NUMERIC(6, 2)) AS peso_kg,
        sprites__other__official_artwork__front_default AS url_imagem_oficial,
        sprites__front_default AS url_sprite_classico
    FROM {{ source('bronze', 'raw_pokemon') }}
),

-- Pivot de tipos em leitura única da tabela
tipos_pivoted AS (
    SELECT 
        _dlt_parent_id, 
        MAX(CASE WHEN slot = 1 THEN UPPER(type__name) END) AS tipo_primario,
        MAX(CASE WHEN slot = 2 THEN UPPER(type__name) END) AS tipo_secundario
    FROM {{ source('bronze', 'raw_pokemon__types') }}
    GROUP BY _dlt_parent_id
),

-- Semente com as descrições oficiais em Português (PT-BR)
traducoes_pt AS (
    SELECT 
        pokemon_id,
        descricao_pt
    FROM {{ ref('pokemon_descricoes_pt') }}
)

SELECT 
    b.pokemon_id,
    b.nome_pokemon,
    pt.descricao_pt AS descricao_pokemon,
    b.experiencia_base,
    b.altura_metros,
    b.peso_kg,
    t.tipo_primario,
    t.tipo_secundario,
    b.url_imagem_oficial,
    b.url_sprite_classico,
    b._dlt_id
FROM base b
LEFT JOIN tipos_pivoted t ON b._dlt_id = t._dlt_parent_id
LEFT JOIN traducoes_pt pt ON b.pokemon_id = pt.pokemon_id
