WITH silver AS (
    SELECT 
        pokemon_id,
        nome_pokemon,
        descricao_pokemon,
        tipo_primario,
        tipo_secundario,
        altura_metros,
        peso_kg,
        experiencia_base,
        url_imagem_oficial,
        url_sprite_classico,
        _dlt_id
    FROM {{ ref('silver_pokemon') }}
),

stats_pivoted AS (
    SELECT 
        _dlt_parent_id,
        MAX(CASE WHEN stat__name = 'hp' THEN base_stat END) AS hp,
        MAX(CASE WHEN stat__name = 'attack' THEN base_stat END) AS ataque,
        MAX(CASE WHEN stat__name = 'defense' THEN base_stat END) AS defesa,
        MAX(CASE WHEN stat__name = 'special-attack' THEN base_stat END) AS ataque_especial,
        MAX(CASE WHEN stat__name = 'special-defense' THEN base_stat END) AS defesa_especial,
        MAX(CASE WHEN stat__name = 'speed' THEN base_stat END) AS velocidade
    FROM {{ source('bronze', 'raw_pokemon__stats') }}
    GROUP BY _dlt_parent_id
)

SELECT
    s.pokemon_id,
    s.nome_pokemon,
    s.descricao_pokemon,
    s.tipo_primario,
    s.tipo_secundario,

    -- 1. Cor do Tipo Primário
    CASE s.tipo_primario
        WHEN 'FIRE' THEN '#F08030'
        WHEN 'WATER' THEN '#6890F0'
        WHEN 'GRASS' THEN '#78C850'
        WHEN 'ELECTRIC' THEN '#F8D030'
        WHEN 'NORMAL' THEN '#A8A878'
        WHEN 'ICE' THEN '#98D8D8'
        WHEN 'FIGHTING' THEN '#C03028'
        WHEN 'POISON' THEN '#A040A0'
        WHEN 'GROUND' THEN '#E0C068'
        WHEN 'FLYING' THEN '#A890F0'
        WHEN 'PSYCHIC' THEN '#F85888'
        WHEN 'BUG' THEN '#A8B820'
        WHEN 'ROCK' THEN '#B8A038'
        WHEN 'GHOST' THEN '#705898'
        WHEN 'DRAGON' THEN '#7038F8'
        WHEN 'STEEL' THEN '#B8B8D0'
        WHEN 'FAIRY' THEN '#EE99AC'
        ELSE '#777777'
    END AS cor_hex_tipo_primario,

    -- 2. Cor do Tipo Secundário (Camufla na cor do primário se monotipo ou string vazia)
    CASE COALESCE(NULLIF(TRIM(s.tipo_secundario), ''), s.tipo_primario)
        WHEN 'FIRE' THEN '#F08030'
        WHEN 'WATER' THEN '#6890F0'
        WHEN 'GRASS' THEN '#78C850'
        WHEN 'ELECTRIC' THEN '#F8D030'
        WHEN 'NORMAL' THEN '#A8A878'
        WHEN 'ICE' THEN '#98D8D8'
        WHEN 'FIGHTING' THEN '#C03028'
        WHEN 'POISON' THEN '#A040A0'
        WHEN 'GROUND' THEN '#E0C068'
        WHEN 'FLYING' THEN '#A890F0'
        WHEN 'PSYCHIC' THEN '#F85888'
        WHEN 'BUG' THEN '#A8B820'
        WHEN 'ROCK' THEN '#B8A038'
        WHEN 'GHOST' THEN '#705898'
        WHEN 'DRAGON' THEN '#7038F8'
        WHEN 'STEEL' THEN '#B8B8D0'
        WHEN 'FAIRY' THEN '#EE99AC'
        ELSE '#777777'
    END AS cor_hex_tipo_secundario,

    s.altura_metros,
    s.peso_kg,
    s.experiencia_base,
    s.url_imagem_oficial,
    s.url_sprite_classico,

    -- Atributos de Batalha
    st.hp,
    st.ataque,
    st.defesa,
    st.ataque_especial,
    st.defesa_especial,
    st.velocidade,

    -- Soma segura de combate com COALESCE defensivo
    (
        COALESCE(st.hp, 0) +
        COALESCE(st.ataque, 0) +
        COALESCE(st.defesa, 0) +
        COALESCE(st.ataque_especial, 0) +
        COALESCE(st.defesa_especial, 0) +
        COALESCE(st.velocidade, 0)
    ) AS total_status_batalha,

    -- Tratamento defensivo contra nulos no peso
    CASE 
        WHEN s.peso_kg IS NULL  THEN 'Desconhecido'
        WHEN s.peso_kg >= 100.0 THEN 'Pesado (+100kg)'
        WHEN s.peso_kg >= 30.0  THEN 'Medio (30-100kg)'
        ELSE 'Leve (<30kg)'
    END AS porte_fisico
FROM silver s
JOIN stats_pivoted st ON s._dlt_id = st._dlt_parent_id
ORDER BY s.pokemon_id ASC
