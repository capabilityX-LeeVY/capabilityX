SELECT 
  COUNT(CASE WHEN failed_steps = 0 THEN 1 END) as success,
  COUNT(CASE WHEN failed_steps > 0 THEN 1 END) as fail
FROM (
  SELECT 
    test_case,
    report_id,
    COUNT(CASE WHEN navigate_result LIKE '%Failed%' THEN 1 END) as failed_steps
  FROM TestCaseNavigateReport
  WHERE DATE(step_start_time) = CURDATE()
    AND test_suite = COALESCE(
      NULLIF('${test_suite}', ''), 
      test_suite
    )
    AND device_name = COALESCE(
      NULLIF('${device_name}', ''), 
      device_name
    )
  GROUP BY test_case, report_id
) test_case_summary;
