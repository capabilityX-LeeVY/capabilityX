SELECT 
    control_name AS "Control Name",
    
    CONCAT(
        CASE 
            WHEN main_cpu > 80 THEN '🔴 '
            WHEN main_cpu > 50 THEN '🟡 '
            ELSE '🟢 '
        END,
        main_cpu, '%'
    ) AS "Main CPU Usage",
    
    CONCAT(
        CASE 
            WHEN main_mem > 1000 THEN '🔴 '
            WHEN main_mem > 500 THEN '🟡 '
            ELSE '🟢 '
        END,
        FORMAT(main_mem, 2), ' MB'
    ) AS "Main Memory Usage"
    
FROM TestCasePerformanceReport 
WHERE report_id = COALESCE(
    NULLIF('$report_id', ''), 
    (SELECT report_id 
     FROM TestCasePerformanceReport 
     WHERE test_suite = COALESCE(
         NULLIF('${test_suite}', ''), 
         test_suite
     )
     AND device_name = COALESCE(
         NULLIF('${device_name}', ''), 
         device_name
     )
     ORDER BY created_at DESC 
     LIMIT 1)
)
AND test_suite = COALESCE(
    NULLIF('${test_suite}', ''), 
    test_suite
)
AND device_name = COALESCE(
    NULLIF('${device_name}', ''), 
    device_name
)
ORDER BY created_at ASC;
