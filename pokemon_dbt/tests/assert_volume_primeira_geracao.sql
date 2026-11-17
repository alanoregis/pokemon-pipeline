-- Regra de Volume: O teste passa se retornar 0 linhas.
-- Se o total for diferente de 151, a query retorna 1 linha e o dbt acusa FALHA.

SELECT 
    COUNT(*) AS total_pokemons
FROM {{ ref('gold_pokemon') }}
HAVING COUNT(*) != 151