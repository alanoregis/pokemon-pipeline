-- Nenhum Pokémon de batalha pode ter atributos zerados ou negativos
SELECT 
    pokemon_id,
    nome_pokemon,
    hp,
    ataque,
    defesa,
    velocidade,
    total_status_batalha
FROM {{ ref('gold_pokemon') }}
WHERE hp <= 0 
   OR ataque <= 0 
   OR defesa <= 0 
   OR velocidade <= 0
   OR total_status_batalha < 150