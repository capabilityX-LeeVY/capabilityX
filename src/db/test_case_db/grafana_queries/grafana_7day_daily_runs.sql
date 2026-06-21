SELECT 
    DATE(step_start_time) as time,
    test_suite,
    device_name,
    COUNT(DISTINCT report_id) as "Daily Test Runs"
FROM TestCaseNavigateReport 
WHERE step_start_time >= DATE_SUB(NOW(), INTERVAL 7 DAY)
  AND step_start_time IS NOT NULL
  AND test_suite = COALESCE(
      NULLIF('${test_suite}', ''), 
      test_suite
  )
  AND device_name = COALESCE(
      NULLIF('${device_name}', ''), 
      device_name
  )
GROUP BY DATE(step_start_time), test_suite, device_name
ORDER BY DATE(step_start_time) ASC, test_suite, device_name;
