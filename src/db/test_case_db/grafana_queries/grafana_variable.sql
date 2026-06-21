SELECT DISTINCT device_name as __text, device_name as __value
FROM TestCaseNavigateReport 
WHERE device_name IS NOT NULL 
  AND device_name != ''
ORDER BY device_name;

SELECT DISTINCT name as __text, name as __value
FROM TestSuites 
WHERE name IS NOT NULL 
  AND name != ''
ORDER BY name;