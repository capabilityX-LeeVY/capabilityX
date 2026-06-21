SELECT 
  locate_control_name,
  ui_response_time_ms
FROM TestCaseNavigateReport 
WHERE ui_response_enabled = TRUE
  AND ui_response_time_ms IS NOT NULL
  AND locate_control_name IS NOT NULL
  AND locate_control_name = 'Start meeting'
  AND device_name = COALESCE(
    NULLIF('${device_name}', ''), 
    device_name
  )
  AND report_id = (
    SELECT report_id 
    FROM TestCaseNavigateReport 
    WHERE ui_response_enabled = TRUE
      AND ui_response_time_ms IS NOT NULL
      AND locate_control_name = 'Start meeting'
      AND device_name = COALESCE(
        NULLIF('${device_name}', ''), 
        device_name
      )
    ORDER BY step_start_time DESC 
    LIMIT 1
  )
ORDER BY ui_response_time_ms DESC;

SELECT 
  ROW_NUMBER() OVER (ORDER BY step_start_time ASC) as measurement_count,
  ui_response_time_ms as response_time,
  report_id,
  device_name
FROM TestCaseNavigateReport 
WHERE ui_response_enabled = TRUE
  AND ui_response_time_ms IS NOT NULL
  AND locate_control_name = 'Start meeting'
  AND device_name = COALESCE(
    NULLIF('${device_name}', ''), 
    device_name
  )
  AND report_id = (
    SELECT report_id 
    FROM TestCaseNavigateReport 
    WHERE ui_response_enabled = TRUE
      AND ui_response_time_ms IS NOT NULL
      AND locate_control_name = 'Start meeting'
      AND device_name = COALESCE(
        NULLIF('${device_name}', ''), 
        device_name
      )
    ORDER BY step_start_time DESC 
    LIMIT 1
  )
ORDER BY step_start_time ASC;