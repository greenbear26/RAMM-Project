USE ramm_lobbying;

-- Seed data: lobby model params (kept from original file)
INSERT INTO lobby_model_weights (model_id, beta_vals) VALUES
(123, '[ 0.41126802,  0.58711135,  0.67997586, -0.66412345,  0.62023535,  0.33219446]');

INSERT INTO lobby_model_scaler (sequence_number, feature_means, feature_stds) VALUES
(1, '[8.347685560354913, 1.1053668826056304, 2.4963675958188154, 388.99390026132403, 0.2435540069686411, 0.7203832752613241]', '[5.082187775240837, 1.4776816842117488, 19.564305484424175, 27749.30922460419, 0.42922657496730116, 0.4488108866606195]');

-- Country indicator seeds (fixed column names and numeric values)
INSERT INTO country_indicator(country,country_code,gdp_usd,population,inflation,gdp_per_capita) VALUES ('Austria','AUT',473221298968.216,9041851,8.54686993188457,52336.77252237578);
INSERT INTO country_indicator(country,country_code,gdp_usd,population,inflation,gdp_per_capita) VALUES ('Belgium','BEL',591085783326.267,11680210,9.597511728725,50605.749667708624);
INSERT INTO country_indicator(country,country_code,gdp_usd,population,inflation,gdp_per_capita) VALUES ('Bulgaria','BGR',90506153293.6733,6465097,15.3252589264367,13999.194953095568);
INSERT INTO country_indicator(country,country_code,gdp_usd,population,inflation,gdp_per_capita) VALUES ('Croatia','HRV',71196498671.1145,3855641,10.7805806758686,18465.541442036356);
INSERT INTO country_indicator(country,country_code,gdp_usd,population,inflation,gdp_per_capita) VALUES ('Cyprus','CYP',31218038929.0919,1331370,8.39548297993334,23448.05645995621);
INSERT INTO country_indicator(country,country_code,gdp_usd,population,inflation,gdp_per_capita) VALUES ('Denmark','DNK',400114306337.077,5903037,7.69656699889259,67781.09409395147);
INSERT INTO country_indicator(country,country_code,gdp_usd,population,inflation,gdp_per_capita) VALUES ('Estonia','EST',38226641740.29,1348840,19.3982634080616,28340.382654940542);
INSERT INTO country_indicator(country,country_code,gdp_usd,population,inflation,gdp_per_capita) VALUES ('Finland','FIN',280253099309.34,5556106,7.12350773301402,50440.56022497411);
INSERT INTO country_indicator(country,country_code,gdp_usd,population,inflation,gdp_per_capita) VALUES ('France','FRA',2794788137066.94,68184457,5.22236748369725,40988.63964065799);
INSERT INTO country_indicator(country,country_code,gdp_usd,population,inflation,gdp_per_capita) VALUES ('Germany','DEU',4201021706478.62,83177813,6.87257438551096,50506.51796385438);
INSERT INTO country_indicator(country,country_code,gdp_usd,population,inflation,gdp_per_capita) VALUES ('Greece','GRC',217990189600.69,10436882,9.64525981280642,20886.524308762906);
INSERT INTO country_indicator(country,country_code,gdp_usd,population,inflation,gdp_per_capita) VALUES ('Hungary','HUN',177002580544.155,9605074,14.6081439492433,18428.02882561394);
INSERT INTO country_indicator(country,country_code,gdp_usd,population,inflation,gdp_per_capita) VALUES ('Ireland','IRL',548341794599.09,5212836,7.82945736434105,105190.68595273091);
INSERT INTO country_indicator(country,country_code,gdp_usd,population,inflation,gdp_per_capita) VALUES ('Italy','ITA',2104067630319.46,59013667,8.20128991161718,35653.90421034944);
INSERT INTO country_indicator(country,country_code,gdp_usd,population,inflation,gdp_per_capita) VALUES ('Latvia','LVA',38003198508.9107,1879383,17.3102830198815,20221.103686109058);
INSERT INTO country_indicator(country,country_code,gdp_usd,population,inflation,gdp_per_capita) VALUES ('Lithuania','LTU',71033884499.7824,2831639,19.7050461518394,25085.784063499053);
INSERT INTO country_indicator(country,country_code,gdp_usd,population,inflation,gdp_per_capita) VALUES ('Luxembourg','LUX',80801680397.0139,653103,6.33600807777919,123719.65891599625);
INSERT INTO country_indicator(country,country_code,gdp_usd,population,inflation,gdp_per_capita) VALUES ('Malta','MLT',18928276162.4131,531113,6.15375621933037,35638.88694574055);
INSERT INTO country_indicator(country,country_code,gdp_usd,population,inflation,gdp_per_capita) VALUES ('Netherlands','NLD',1046540797548.64,17700982,10.0012078753473,59123.31855648687);
INSERT INTO country_indicator(country,country_code,gdp_usd,population,inflation,gdp_per_capita) VALUES ('Poland','POL',695607470875.276,36821749,14.4294507575758,18891.21211692785);
INSERT INTO country_indicator(country,country_code,gdp_usd,population,inflation,gdp_per_capita) VALUES ('Portugal','PRT',256898677175.024,10434332,7.83269124233323,24620.519758718045);
INSERT INTO country_indicator(country,country_code,gdp_usd,population,inflation,gdp_per_capita) VALUES ('Romania','ROU',295319437556.988,19048502,13.7954887432521,15503.551804597966);
INSERT INTO country_indicator(country,country_code,gdp_usd,population,inflation,gdp_per_capita) VALUES ('Slovenia','SVN',59899117741.0022,2112076,8.83369886749452,28360.30414672682);
INSERT INTO country_indicator(country,country_code,gdp_usd,population,inflation,gdp_per_capita) VALUES ('Spain','ESP',1448850658406.62,47786102,8.39057634118626,30319.49871966163);
INSERT INTO country_indicator(country,country_code,gdp_usd,population,inflation,gdp_per_capita) VALUES ('Sweden','SWE',575071237640.921,10486941,8.36929098869189,54836.89072351232);
