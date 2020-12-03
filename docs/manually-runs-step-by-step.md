# Passo a passo para executar de forma manual

Descreve o que deve ser seguido para a geração das estatísticas mensais de queimadas no Bioma Amazônia em relação aos desmatamentos (PRODES + DETER) e em relação aos imóveis ruais do CAR.

## O que temos aqui?

Um conjunto de scripts que permite automatizar a geração dos dados estatisticos mencionados acima.

A forma atual de execução é manual pois os dados de focos de Queimadas não estão abertos para download via WFS, que é a forma automatizada de download implementada neste processo. Sendo assim, é ncessário baixar os dados de focos de queimadas do mês de interesse, de forma manual, na pasta de dados onde o script poderá ler. Detalhes na seção de pré-requisitos.


## pré-requisitos

Sáo pré-requisitos para a execução dos scripts:

- Acesso SSH ao servidor onde os scripts estão instalados;
- Obtenção do shapefile de desmatamentos DETER do mês de interesse;
- Obtenção do shapefile de focos de Queimadas do mês de interesse;
- Copia dos arquivos de identificação dos shapefiles para junto dos shapes de interesse (ver acquisition_data_control na sessão passo a passo);
- Verificação dos dados de configuração de acesso ao banco Postgres (opcional);
- Verificação da data de referência para o DETER (opcional - necessário apenas quando novos dados PRODES forem incorporados no tif de desmatamentos recentes);
- Os arquivos em formato TIF, definidos como entrada dos processos, devem existir no diretório raiz: /docker/data/fires/raster
  - car_categories_buffer.tif
  - prodes_desmate_consolidado_pv10_dist_fat.tif
  - prodes_floresta_pv1.tif
  - prodes_desmate_recente_pv15.tif

## Passo a passo

O primeiro passo é identificar se os dados do DETER para o mês de interesse já estão completos na base oficial no TerraBrasilis.
Em caso afirmativo, o processo poderá ser inciado. Os dados do DETER serão baixados via WFS pelos scripts.

O script usa o seguinte diretório base para ler e escrever: /docker/data/fires/raster

- Baixar os dados de focos de queimadas no diretório /docker/data/fires/raster/focuses/
- Criar um arquivo texto de nome acquisition_data_control no diretório /docker/data/fires/raster/focuses/
  - Neste arquivo, inserir o seguinte conteúdo referente a data inicial e final do mês e o número de linhas existentes na tabela do shape:
  ```txt
  END_DATE="2020-10-31T23:59:59"
  START_DATE="2020-10-01T00:00:00"
  numberMatched=8784
  ```
  * este é um exemplo, os valores corretos para o shapefile do mês deve ser fornecido.
- (Passo opcional) para o caso de alterações nos dados de conexão com o banco ou na data de referência do PRODES/DETER;
  - Se necessário, atualizar as informações dos arquivos pgconfig e deter_view_date em /docker/data/fires/raster/config/
- Rodar o comando para iniciar o processo:
  ```sh
  manually_generate_fires_data.sh
  ```

# Pós-processamento

Os scripts geram logs de saída dos processos executados e arquivos raster (TIFs) intermediários. Todos estes arquivos ficam no diretório de trabalho:
 - /docker/data/fires/raster/
 - /docker/data/fires/raster/alerts/
 - /docker/data/fires/raster/focuses/

Para verificar os resultados no banco de dados, a seguintes consultas (SQL) podem ser utilizadas:

```sql
SELECT COUNT(*), MAX(view_date) FROM public.deter_all_amazonia WHERE view_date>'2020-09-30'

SELECT COUNT(*), MAX(datahora) FROM public.focos_aqua_referencia WHERE classe_car IS NULL
-- OR
SELECT COUNT(*), MAX(datahora) FROM public.focos_aqua_referencia WHERE datahora>'2020-09-30'
```

## Caso necessário executar novamente

Caso tenha ocorrido algum erro, ou simplesmente queira repetir o processamento, é necessário refazer os passos da sessão passo a passo, mas antes o banco de dados deve ser verificado e se necessário, os dados inseridos anteriormente devem ser removidos.

- O script irá rodar apenas se os dados de entrada (SHPs) disponíveis nos diretórios ~/alerts/ e ~/focuses/ não estiverem registrados na tabela de controle public.acquisition_data_control;
- Limpar a tabela de controle com a consulta (SQL) a seguir:
  ```sql
  WITH a_date AS (
    SELECT extract(month from now())-1 as a_month, extract(year from now()) as a_year
  ), last_month AS (
    SELECT (a_year || '-' || a_month || '-01')::date as lm FROM a_date
  )
  SELECT * FROM public.acquisition_data_control WHERE end_date>(SELECT lm FROM last_month)
  -- DELETE FROM public.acquisition_data_control WHERE end_date>(SELECT lm FROM last_month)
  ```
  - O SELECT deve ser comentado e o DELETE descomentado para efetivar a limpeza.

- Remover os dados das tabelas de alertas e focos usando as seguintes consultas:
  ```sql
  SELECT COUNT(*), MAX(view_date) FROM public.deter_all_amazonia WHERE view_date>'2020-09-30'

  -- DELETE FROM public.deter_all_amazonia WHERE view_date>'2020-09-30'

  SELECT COUNT(*), MAX(datahora) FROM public.focos_aqua_referencia WHERE classe_car IS NULL

  SELECT COUNT(*), MAX(datahora) FROM public.focos_aqua_referencia WHERE datahora>='2020-10-01'

  -- DELETE FROM public.focos_aqua_referencia WHERE classe_prodes IS NULL
  ```
  - Consultas para verificação antes da remoção. Ajuste como necessário para o mês de interesse.
  - Atenção com as datas do filtro para remover apenas o necessário;

- Seguir o passo a passo no que for necessário;

## Baixar os dados via HTTP

É possível baixar os dados intermediários do diretório de trabalho do script via navegador usando o endereço seguinte (apenas interno ao INPE):

http://150.163.2.93

* Dica: comprima os arquivos TIF antes de baixar, diretamente na linha de comandos do servidor acessado via SSH.

# Atualizar os dados no Dashboard

A atualização dos dados no dashboard deve ser executada no servidor onde o dashboard está instalado rodando um script específico para esse fim.
Este script irá baixar um arquivo JSON para cada tema, Desmatamento ou CAR, diretamente de um serviço WFS proveniente de camadas específicas no GeoServer do TerraBrasilis que apontam para o banco de publicação no qual os dados gerados por este script são inseridos.