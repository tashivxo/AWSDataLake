-- ============================================================
-- Olympic Data Lake - Athena Queries
-- Database: olympic_db
-- ============================================================


-- 1. Total Medals by Country (Both Seasons)
-- Query ID: 3aede9a1-77e6-407f-a3d2-1b7fdac24112
SELECT Code, Season, COUNT(*) as total_medals,
    SUM(CASE WHEN Medal = 'Gold' THEN 1 ELSE 0 END) as gold,
    SUM(CASE WHEN Medal = 'Silver' THEN 1 ELSE 0 END) as silver,
    SUM(CASE WHEN Medal = 'Bronze' THEN 1 ELSE 0 END) as bronze
FROM olympic_db.processed_events
GROUP BY Code, Season
ORDER BY total_medals DESC
LIMIT 25;


-- 2. Gender Participation Over Time
-- Query ID: fda3f52e-9b6b-48f5-b075-37d652c94097
SELECT Year, Season, Gender, COUNT(DISTINCT Athlete) as athlete_count
FROM olympic_db.processed_events
GROUP BY Year, Season, Gender
ORDER BY Year, Season;


-- 3. GDP vs Medal Performance (JOIN with countries)
-- Query ID: 386200e7-ce61-46ec-9e4e-27520081a5de
SELECT c.Country, c.Code, c.gdp_per_capita, COUNT(*) as total_medals
FROM olympic_db.processed_events e
JOIN olympic_db.processed_countries c ON e.Code = c.Code
GROUP BY c.Country, c.Code, c.gdp_per_capita
ORDER BY total_medals DESC
LIMIT 30;


-- 4. Population-Normalized Medal Count
-- Query ID: 47908ef8-9898-452f-aea2-590d5c211048
SELECT c.Country, c.Code, c.Population, COUNT(*) as total_medals,
    ROUND(COUNT(*) * 1000000.0 / c.Population, 2) as medals_per_million
FROM olympic_db.processed_events e
JOIN olympic_db.processed_countries c ON e.Code = c.Code
WHERE c.Population > 0
GROUP BY c.Country, c.Code, c.Population
ORDER BY medals_per_million DESC
LIMIT 25;


-- 5. Sport Evolution (New Sports Over Decades)
-- Query ID: 79152b6b-c5fb-4e0b-b95e-bb68ef86ce90
SELECT Sport, MIN(Year) as first_appeared, MAX(Year) as last_appeared,
    COUNT(DISTINCT Year) as editions,
    COUNT(DISTINCT Discipline) as disciplines
FROM olympic_db.processed_events
GROUP BY Sport
ORDER BY first_appeared;


-- 6. Create Enriched Reusable View
-- Query ID: 5daefc0f-a8d2-4d49-ba57-faa8df69f39d
CREATE OR REPLACE VIEW olympic_db.enriched_medals AS
SELECT e.*,
    c.Country as country_name,
    c.Population,
    c.gdp_per_capita
FROM olympic_db.processed_events e
LEFT JOIN olympic_db.processed_countries c ON e.Code = c.Code;


-- 7. Query the Enriched View (use after running query 6)
SELECT *
FROM olympic_db.enriched_medals
LIMIT 100;
