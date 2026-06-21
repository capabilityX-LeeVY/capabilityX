"""
get_guest_join_metrics.py

This module provides functionality to query Webex OneView Service API 
for meeting join metrics and results.

Note: For log parsing and correlation ID extraction, see log_parser.py
"""

import requests
import json
import os
import sys
import tempfile
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()
pythonpath = os.getenv("PYTHONPATH")
if pythonpath:
    full_path = os.path.abspath(pythonpath)
    if full_path not in sys.path:
        sys.path.insert(0, full_path)
from common.startup import token_initializer
from typing import Dict, Any, Optional
from common.utils.logger import LOGGER_INFO, LOGGER_DEBUG, LOGGER_ERROR, LOGGER_WARNING

# Import log parsing functions from separate module
from test_space.test_functions.basic_functions.webex_app_log_parser import (
    get_correlation_id_from_log,
    get_all_correlation_ids_from_log,
    search_log_for_pattern
)

_CORRELATION_ID_FILE = Path(tempfile.gettempdir()) / "wrs_shared_correlation_id.txt"


def _load_correlation_id_store() -> list[str]:
    """Load all saved correlation IDs from the temp store."""
    if not _CORRELATION_ID_FILE.exists():
        return []

    raw_text = _CORRELATION_ID_FILE.read_text(encoding="utf-8").strip()
    if not raw_text:
        return []

    try:
        data = json.loads(raw_text)
        if isinstance(data, list):
            return [str(item).strip() for item in data if str(item).strip()]
    except json.JSONDecodeError:
        # Backward compatibility with the old single-value format
        return [raw_text]

    return []


def _save_correlation_id_store(correlation_ids: list[str]) -> None:
    """Persist the full correlation ID list to the temp store."""
    _CORRELATION_ID_FILE.write_text(
        json.dumps(correlation_ids, ensure_ascii=True, indent=2),
        encoding="utf-8",
    )


class MeetingMetricsClient:
    """
    Client for querying Webex OneView Service API for meeting metrics and join results.
    
    Attributes:
        bearer_token (str): The Bearer token for authentication
        api_url (str): The OneView Service API endpoint
    """
    
    def __init__(self, bearer_token: Optional[str] = None):
        """
        Initialize the MeetingMetricsClient.
        
        Args:
            bearer_token (str, optional): Bearer token for authentication.
                                         If not provided, will auto-fetch from token_initializer.
        """
        self.api_url = "https://oneviewservice.webex.com/api/internal/support/getQuery"
        self._bearer_token = bearer_token
    
    @property
    def bearer_token(self) -> str:
        """Get the bearer token, auto-fetching if not already set."""
        if not self._bearer_token:
            self._bearer_token = token_initializer.update_token('controlhub')
        if not self._bearer_token:
            raise ValueError("Failed to obtain bearer token from token_initializer")
        return self._bearer_token
    
    def get_meeting_join_result(
        self,
        columns = ["outcome", "mediaOutcome", "resultName", "identifiers_webexSiteName"]
    ) -> Dict[str, Any]:
        """
        Query Webex OneView Service API to get meeting join result.
        Automatically extracts correlation_id from the Webex app log file.
        
        Args:
            columns (list, optional): List of columns to query (default: ["outcome", "mediaOutcome", "resultName", "identifiers_webexSiteName"])
        
        Returns:
            Dict[str, Any]: JSON response containing the query results
            
        Example:
            >>> client = MeetingMetricsClient()
            >>> result = client.get_meeting_join_result()
            >>> print(result)
        
        Raises:
            requests.exceptions.RequestException: If the API request fails
            ValueError: If correlation_id cannot be extracted from log
        """
        # Get correlation_id from log file
        correlation_id = get_correlation_id_from_log()
        # correlation_id = "d34f91da-49b4-4c18-ad5e-16a340ba6594"
        # correlation_id = "faad13a8-2119-4a30-83ec-c4b173821a45"
        if not correlation_id:
            raise ValueError("Failed to extract correlation_id from log file")
        
        LOGGER_INFO(f"🔍 Using correlation_id from log: {correlation_id}")
        
        headers = {
            "authorization": f"Bearer {self.bearer_token}",
            "content-type": "application/json"
        }
        
        # Build the SQL query
        # query = (
        #     f"select outcome as prejoinResult, mediaOutcome as mediaResult, resultName, identifiers_webexSiteName from callanalyzer_result_metrics "
        #     f"where identifiers_correlationId = '{correlation_id}' "
        #     f"and resultName = '{result_name}'"
        # )
        #columns = ["outcome", "mediaOutcome", "resultName", "identifiers_webexSiteName"]
        query = (
            f"select {', '.join(columns)} from callanalyzer_result_metrics "
            f"where identifiers_correlationId = '{correlation_id}' "
            "and (resultName = 'join.result' or resultName = 'pre.join.result')"
        )
        
        payload = {
            "params": {
                "variables": {
                    "query": query
                }
            }
        }
        
        try:
            response = requests.post(self.api_url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            LOGGER_ERROR(f"❌ Error querying OneView Service API: {e}")
            raise

    def get_meeting_metrics(
        self,
        correlation_id: str,
        custom_query: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute a custom query or default query to get meeting metrics.
        
        Args:
            correlation_id (str): The correlation ID of the meeting
            custom_query (str, optional): Custom SQL query. If not provided, uses default join result query
        
        Returns:
            Dict[str, Any]: JSON response containing the query results
            
        Example:
            >>> client = MeetingMetricsClient()
            >>> correlation_id = "e2d434ea-cbd3-487f-822b-b0a3707c77a1"
            >>> 
            >>> # Use default query
            >>> result = client.get_meeting_metrics(correlation_id)
            >>> 
            >>> # Use custom query
            >>> custom = "select * from callanalyzer_result_metrics where identifiers_correlationId = 'xxx'"
            >>> result = client.get_meeting_metrics(correlation_id, custom_query=custom)
        """
        headers = {
            "authorization": f"Bearer {self.bearer_token}",
            "content-type": "application/json"
        }
        
        # Use custom query or build default query
        if custom_query:
            query = custom_query
        else:
            query = (
                f"select outcome from callanalyzer_result_metrics "
                f"where identifiers_correlationId = '{correlation_id}' "
                f"and resultName = 'join.result'"
            )
        
        payload = {
            "params": {
                "variables": {
                    "query": query
                }
            }
        }
        
        try:
            response = requests.post(self.api_url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            LOGGER_ERROR(f"❌ Error querying OneView Service API: {e}")
            raise

    @staticmethod
    def extract_outcome_value(api_response: Dict[str, Any]) -> Optional[str]:
        """
        Extract the outcome value from the API response.
        
        Args:
            api_response (Dict[str, Any]): The JSON response from the API
        
        Returns:
            Optional[str]: The outcome value if found, None otherwise
        """
        try:
            # Navigate through the response structure to get the outcome
            # Adjust this based on actual API response structure
            if "data" in api_response:
                data = api_response["data"]
                if isinstance(data, list) and len(data) > 0:
                    if "outcome" in data[0]:
                        return data[0]["outcome"]
            return None
        except (KeyError, IndexError, TypeError) as e:
            LOGGER_WARNING(f"⚠️ Warning: Could not extract outcome value: {e}")
            return None


# Example usage
if __name__ == "__main__":
    # Example 1: Extract correlation ID from log file
    print("=" * 60)
    print("Example 1: Extract Correlation ID from Log")
    print("=" * 60)
    
    log_file = "C:/logs/webex_meeting.log"  # Replace with your log file path
    
    # Get single correlation ID
    # correlation_id = get_correlation_id_from_log()
    correlation_id = "d34f91da-49b4-4c18-ad5e-16a340ba6594"
    
    # Or get all correlation IDs
    # all_ids = get_all_correlation_ids_from_log(log_file)
    
    print("\n")
    
    # Example 2: Query OneView Service API with correlation ID
    print("=" * 60)
    print("Example 2: Query Meeting Join Result")
    print("=" * 60)
    
    if correlation_id:
        try:
            # Create client instance
            client = MeetingMetricsClient()
            
            # Get meeting join result (correlation_id is automatically extracted from log)
            print(f"🔍 Querying meeting join result...")
            result = client.get_meeting_join_result()
            print(f"✅ API Response: {json.dumps(result, indent=2)}")
                
        except Exception as e:
            print(f"❌ Error: {e}")
    else:
        print("⚠️ No correlation ID found, skipping API query")
    
    print("\n")
    
    # Example 3: Search log for custom pattern
    print("=" * 60)
    print("Example 3: Search Log for Custom Pattern")
    print("=" * 60)
    
    # Search for any pattern in the log
    matches = search_log_for_pattern(
        log_file, 
        pattern="event flow id",
        context_lines=1
    )
    
    if matches:
        print(f"\n📋 First match details:")
        first_match = matches[0]
        print(f"   Line: {first_match['line_number']}")
        print(f"   Content: {first_match['match']}")


# ============================================================================
# Module-level function for function.json registration
# ============================================================================

def get_meeting_join_result(
    columns: Optional[list] = None
) -> Dict[str, Any]:
    """
    Module-level wrapper function for getting meeting join result.
    This function is registered in function.json and can be called by the test framework.
    
    Args:
        columns (list, optional): List of columns to query. 
                                 If None, uses default columns.
    
    Returns:
        Dict[str, Any]: JSON response containing the query results
        
    Example:
        >>> result = get_meeting_join_result()
        >>> result = get_meeting_join_result(columns=["outcome", "mediaOutcome"])
    """
    if columns is None:
        columns = ["outcome", "mediaOutcome", "resultName", "identifiers_webexSiteName"]
    
    client = MeetingMetricsClient()
    return client.get_meeting_join_result(columns=columns)


def save_current_correlation_id() -> str:
    """Extract the current correlation ID from log, append it to the shared store, and return it."""
    correlation_id = get_correlation_id_from_log()
    if not correlation_id:
        raise ValueError("Failed to extract correlation_id from log file")

    correlation_ids = _load_correlation_id_store()
    if correlation_id not in correlation_ids:
        correlation_ids.append(correlation_id)
        _save_correlation_id_store(correlation_ids)

    return correlation_id


def load_saved_correlation_id() -> str:
    """Load the most recently saved correlation ID from the shared store."""
    correlation_ids = _load_correlation_id_store()
    if not correlation_ids:
        return ""
    return correlation_ids[-1]


def load_all_saved_correlation_ids() -> str:
    """Load all saved correlation IDs from the shared store as a JSON array string."""
    correlation_ids = _load_correlation_id_store()
    return json.dumps(correlation_ids, ensure_ascii=True)


def clear_saved_correlation_ids() -> str:
    """Clear the shared correlation ID store."""
    _save_correlation_id_store([])
    return "cleared"
