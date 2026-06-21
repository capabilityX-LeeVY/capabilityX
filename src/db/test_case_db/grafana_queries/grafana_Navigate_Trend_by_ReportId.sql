-- Navigation trend chart by report_id
-- Shows success/failure counts for each test execution (report_id)
-- X-axis: execution sequence number (each report_id as one node)
-- Y-axis: success/failure counts

SELECT 
  ROW_NUMBER() OVER (ORDER BY MIN(step_start_time) ASC) as execution_sequence,
  report_id,
  CONVERT_TZ(MIN(step_start_time), '+08:00', '+00:00') AS execution_time,
  COUNT(CASE WHEN navigate_result NOT LIKE '%Failed%' AND navigate_result IS NOT NULL AND navigate_result != '' THEN 1 END) as success_count,
  COUNT(CASE WHEN navigate_result LIKE '%Failed%' THEN 1 END) as failure_count,
  COUNT(*) as total_steps,
  test_suite,
  device_name
FROM TestCaseNavigateReport 
WHERE test_suite = COALESCE(
    NULLIF('${test_suite}', ''), 
    test_suite
  )
  AND device_name = COALESCE(
    NULLIF('${device_name}', ''), 
    device_name
  )
  AND step_start_time >= NOW() - INTERVAL 7 DAY  -- Last 7 days
GROUP BY report_id, test_suite, device_name
ORDER BY MIN(step_start_time) ASC;
