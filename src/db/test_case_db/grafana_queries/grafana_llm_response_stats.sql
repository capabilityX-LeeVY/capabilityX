SELECT 
  COUNT(CASE WHEN llm_response NOT LIKE '%fail%' AND llm_response IS NOT NULL AND llm_response != '' THEN 1 END) as success,
  COUNT(CASE WHEN llm_response LIKE '%fail%' THEN 1 END) as fail
FROM TestCaseNavigateReport 
WHERE DATE(step_start_time) = CURDATE()
  AND test_suite = COALESCE(
    NULLIF('${test_suite}', ''), 
    test_suite
  )
  AND device_name = COALESCE(
    NULLIF('${device_name}', ''), 
    device_name
  );
