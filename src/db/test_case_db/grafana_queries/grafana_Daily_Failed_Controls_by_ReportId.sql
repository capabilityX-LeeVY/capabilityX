-- Daily failed controls count by report_id (based on compliance status)
-- Shows the number of non-compliant controls for each test execution (report_id) on current date
-- Grouped by report_id with test_suite and device_name filters

SELECT 
  report_id,
  COUNT(CASE 
    WHEN UPPER(compliance) LIKE '%NON-COMPLIANT%' 
     OR UPPER(compliance) LIKE '%PARTIAL%'
    THEN 1 
  END) as failed_controls_count
FROM ScreenReaderReport 
WHERE DATE(created_at) = CURDATE()  -- Current date only
  AND test_suite = COALESCE(
    NULLIF('${test_suite}', ''), 
    test_suite
  )
  AND device_name = COALESCE(
    NULLIF('${device_name}', ''), 
    device_name
  )
GROUP BY report_id
ORDER BY failed_controls_count DESC;
