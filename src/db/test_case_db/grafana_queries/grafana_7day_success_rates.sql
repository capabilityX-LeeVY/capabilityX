SELECT 
  ROUND(
    (SUM(CASE WHEN llm_response NOT LIKE '%Fail%' AND llm_response IS NOT NULL AND llm_response != '' THEN 1 ELSE 0 END) * 100.0) 
    / NULLIF(SUM(CASE WHEN llm_response IS NOT NULL AND llm_response != '' THEN 1 END), 0), 
    2
  ) as AI,
  
  ROUND(
    (SUM(CASE WHEN navigate_result NOT LIKE '%Failed%' AND navigate_result IS NOT NULL AND navigate_result != '' THEN 1 ELSE 0 END) * 100.0) 
    / NULLIF(SUM(CASE WHEN navigate_result IS NOT NULL AND navigate_result != '' THEN 1 END), 0), 
    2
  ) as nav

FROM TestCaseNavigateReport 
WHERE step_start_time >= NOW() - INTERVAL 7 DAY
  AND test_suite = COALESCE(
      NULLIF('${test_suite}', ''), 
      test_suite
  )
  AND device_name = COALESCE(
      NULLIF('${device_name}', ''), 
      device_name
  );
