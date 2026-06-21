SELECT 
    CONVERT_TZ(step_start_time, '+08:00', '+00:00') AS "Start Time",
    locate_control_name AS "Control Name",
    CASE 
        WHEN navigate_result = 'Success' THEN '✅ Success'
        WHEN navigate_result = 'Failed' THEN '❌ Failed'
        WHEN navigate_result = 'Optional' THEN '⚠️ Optional'
        ELSE navigate_result
    END AS "Result"
FROM TestCaseNavigateReport 
WHERE report_id = COALESCE(
    NULLIF('$report_id', ''), 
    (SELECT report_id 
     FROM TestCaseNavigateReport 
     WHERE test_suite = COALESCE(
         NULLIF('${test_suite}', ''), 
         test_suite
     )
     AND device_name = COALESCE(
         NULLIF('${device_name}', ''), 
         device_name
     )
     ORDER BY step_start_time DESC 
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
ORDER BY step_order ASC;

-- 简化版查询：仅通过report_id查询详细报告
SELECT 
    report_id,
    CONVERT_TZ(step_start_time, '+08:00', '+00:00') AS step_start_time,
    CASE 
        WHEN navigate_result = 'Success' THEN '✅ Success'
        WHEN navigate_result = 'Failed' THEN '❌ Failed'
        WHEN navigate_result = 'Optional' THEN '⚠️ Optional'
        ELSE navigate_result
    END AS "Result",
    test_case,
    test_steps,
    locate_control_name,
    expect_result,
    actual_result,
    device_name,
    device_ip
FROM TestCaseNavigateReport 
WHERE report_id = '${report_id}'
ORDER BY step_start_time DESC, step_order;
