-- Screen Reader Compliance Daily Summary
-- Shows daily compliance statistics similar to navigate check
-- Returns: compliant count and non-compliant count

SELECT 
  COUNT(CASE WHEN failed_compliance = 0 THEN 1 END) as success,
  COUNT(CASE WHEN failed_compliance > 0 THEN 1 END) as fail
FROM (
  SELECT 
    test_case,
    report_id,
    COUNT(CASE WHEN compliance IN ('Non-compliant', 'Partial', 'Unknown') THEN 1 END) as failed_compliance
  FROM ScreenReaderReport
  WHERE DATE(created_at) = CURDATE()
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
