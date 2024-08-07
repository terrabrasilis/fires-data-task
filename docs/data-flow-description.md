## Data flow description

Used to standardize and communicate the data flow used to generate the time series for classifying Active fire based on the deforested areas of PRODES and DETER, the secondary vegetation of TerraClass and the rural property of CAR.

There are two flows to produce the desired data.

 - Active fires x Deforestations;
 - Active fires x CAR;

### Input data

There are five input data used to produce this dataset.

 - Fire data: geographical coordinates of active fires, extracted from images of the reference satellite - AQUA/MODIS afternoon passages - obtained at Portal Queimadas-INPE;
 - Consolidated deforestation: PRODES database aggregating all deforestation already mapped two years ago or more;
 - Recent deforestation: deforested areas mapped by PRODES two years ago or earlier, plus deforestation alerts mapped between the last available PRODES year and the last month for which DETER data is available;
 - Secondary Vegetation: The latest TerraClass secondary vegetation mask for each biome;
 - CAR rural property: the preprocessed Rural Environmental Registry (CAR);


### Output data

The expected result is two attributes for each active fire point.

The first attribute must have one of the valid values ​​for the deforestation-related groups.
```
- Others
- Forest
- Consolidated deforestation
- Recent deforestation
- Secondary Vegetation
```

The second attribute must have one of the valid values ​​for groups related to rural property.
```
- Without CAR
- Smallholdings
- Small
- Average
- Large
```