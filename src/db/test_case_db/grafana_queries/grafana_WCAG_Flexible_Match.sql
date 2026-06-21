-- WCAG Compliance trend chart (Case-insensitive version)
-- Shows compliant and non-compliant counts with flexible matching
-- X-axis: execution sequence number (each report_id as one node)
-- Y-axis: compliant/non-compliant counts

SELECT 
  ROW_NUMBER() OVER (ORDER BY MIN(created_at) ASC) as execution_sequence,
  report_id,
  CONVERT_TZ(MIN(created_at), '+08:00', '+00:00') AS execution_time,
  COUNT(CASE WHEN LOWER(TRIM(compliance)) LIKE '%compliant%' AND LOWER(TRIM(compliance)) NOT LIKE '%non%' THEN 1 END) as compliant_count,
  COUNT(CASE WHEN LOWER(TRIM(compliance)) LIKE '%non-compliant%' OR LOWER(TRIM(compliance)) LIKE '%noncompliant%' THEN 1 END) as non_compliant_count,
  COUNT(CASE WHEN LOWER(TRIM(compliance)) = 'pass' THEN 1 END) as pass_count,
  COUNT(CASE WHEN LOWER(TRIM(compliance)) = 'fail' THEN 1 END) as fail_count,
  COUNT(*) as total_controls,
  test_suite,
  device_name
FROM ScreenReaderReport 
WHERE test_suite = COALESCE(
    NULLIF('${test_suite}', ''), 
    test_suite
  )
  AND device_name = COALESCE(
    NULLIF('${device_name}', ''), 
    device_name
  )
  AND DATE(created_at) >= DATE(NOW() - INTERVAL 7 DAY)  -- Last 7 days
GROUP BY report_id, test_suite, device_name
ORDER BY MIN(created_at) ASC;
