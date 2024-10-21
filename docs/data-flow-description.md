## Data flow description

Used to standardize and communicate the data flow used to generate the time series for classifying Active fire based on the deforested areas of PRODES and DETER, the secondary vegetation of TerraClass and the rural property of CAR.

There are two flows to produce the desired data.

 - [Active fires x Deforestations](./fire-classification-flow-first-flow.png);
 - [Active fires x CAR](./fire-classification-flow-second-flow.png);

### Input data

There are four input data used to produce this dataset.

 - Fire data: geographical coordinates of active fires, extracted from images of the reference satellite - AQUA/MODIS afternoon passages - obtained at Portal Queimadas-INPE;
 - Consolidated deforestation: PRODES database aggregating all deforestation already mapped three years ago or more;
 - Recent deforestation: deforested areas mapped by PRODES three years ago or earlier, plus deforestation alerts mapped between the last available PRODES year and the last month for which DETER data is available;
 - CAR rural property: the preprocessed Rural Environmental Registry (CAR);


### Output data

The expected result is two attributes for each active fire point.

The first attribute must have one of the valid values ​​for the deforestation-related groups.
```
- Others
- Native Vegetation
- Consolidated deforestation
- Recent deforestation
```

The second attribute must have one of the valid values ​​for groups related to rural property.
```
- Without CAR
- Small
- Average
- Large
```