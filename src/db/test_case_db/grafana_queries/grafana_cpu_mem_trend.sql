SELECT 
    CONVERT_TZ(test_time, '+00:00', '+08:00') as "time",
    main_cpu as "Main CPU (%)",
    media_cpu as "Media CPU (%)"
FROM TestCasePerformanceReport 
WHERE report_id = COALESCE(NULLIF('${report_id}', ''), (SELECT report_id FROM TestCasePerformanceReport ORDER BY test_time DESC LIMIT 1))
ORDER BY test_time ASC;

SELECT 
    CONVERT_TZ(test_time, '+00:00', '+08:00') as "time",
    main_mem as "Main Memory (MB)",
    media_mem as "Media Memory (MB)"
FROM TestCasePerformanceReport 
WHERE report_id = COALESCE(NULLIF('${report_id}', ''), (SELECT report_id FROM TestCasePerformanceReport ORDER BY test_time DESC LIMIT 1))
ORDER BY test_time ASC;

SELECT 
    id AS "Step",
    test_case AS "Test Case",
    control_name AS "Control Name",
    
    CONCAT(ROUND(main_mem, 2), ' MB') AS "Main Memory",
    CONCAT(ROUND(media_mem, 2), ' MB') AS "Media Memory",
    CONCAT(ROUND(main_mem + media_mem, 2), ' MB') AS "Total Memory",
    
    CASE 
        WHEN main_mem + media_mem > 1000 THEN '🔴 High (>1GB)'
        WHEN main_mem + media_mem > 500 THEN '🟡 Medium (>500MB)'
        WHEN main_mem + media_mem > 200 THEN '🟢 Normal (>200MB)'
        ELSE '⚪ Low (<200MB)'
    END AS "Memory Status",
    
    CASE 
        WHEN LAG(main_mem + media_mem) OVER (ORDER BY test_time) IS NULL THEN '➡️ Initial'
        WHEN (main_mem + media_mem) > LAG(main_mem + media_mem) OVER (ORDER BY test_time) THEN '📈 Increased'
        WHEN (main_mem + media_mem) < LAG(main_mem + media_mem) OVER (ORDER BY test_time) THEN '📉 Decreased'
        ELSE '➡️ Stable'
    END AS "Memory Trend",

    CONVERT_TZ(test_time, '+08:00', '+00:00') AS "Test Time",
    
    app_version AS "App Version",
    
    CONVERT_TZ(created_at, '+08:00', '+00:00') AS "Created At"
    
FROM TestCasePerformanceReport 
WHERE report_id = COALESCE(
    NULLIF('${report_id}', ''), 
    (SELECT report_id FROM TestCasePerformanceReport ORDER BY test_time DESC LIMIT 1)
)
ORDER BY test_time ASC;

