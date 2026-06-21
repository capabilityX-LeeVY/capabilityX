-- LLM Response trend chart by report_id
-- Shows llm_response success/failure counts for each test execution (report_id)
-- X-axis: execution sequence number (each report_id as one node)
-- Y-axis: llm_response success/failure counts

SELECT 
  ROW_NUMBER() OVER (ORDER BY MIN(step_start_time) ASC) as execution_sequence,
  report_id,
  CONVERT_TZ(MIN(step_start_time), '+08:00', '+00:00') AS execution_time,
  COUNT(CASE WHEN llm_response NOT LIKE '%fail%' AND llm_response IS NOT NULL AND llm_response != '' THEN 1 END) as llm_success_count,
  COUNT(CASE WHEN llm_response LIKE '%fail%' THEN 1 END) as llm_failure_count,
  COUNT(CASE WHEN llm_response IS NOT NULL AND llm_response != '' THEN 1 END) as llm_total_responses,
  ROUND(
    COUNT(CASE WHEN llm_response NOT LIKE '%fail%' AND llm_response IS NOT NULL AND llm_response != '' THEN 1 END) * 100.0 / 
    NULLIF(COUNT(CASE WHEN llm_response IS NOT NULL AND llm_response != '' THEN 1 END), 0), 
    2
  ) as llm_success_rate_percentage,
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
  AND llm_response IS NOT NULL AND llm_response != ''  -- Only include records with llm_response
GROUP BY report_id, test_suite, device_name
ORDER BY MIN(step_start_time) ASC;
