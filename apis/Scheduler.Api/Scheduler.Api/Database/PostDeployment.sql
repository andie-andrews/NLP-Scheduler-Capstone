/*
  DACPAC Post-Deployment script.
  - Executes current restaurant seed upsert script
*/

SET NOCOUNT ON;

:r .\Seed.RestaurantScenario.sql
