-- Connettiti al database giusto (opzionale se lo script viene eseguito nel contesto giusto, ma sicuro)
\c monitoraggio_db;

-- Abilita PostGIS
CREATE EXTENSION IF NOT EXISTS postgis;