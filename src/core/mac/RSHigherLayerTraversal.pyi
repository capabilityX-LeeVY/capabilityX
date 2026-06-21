"""
Type stub file for core/mac/RSHigherLayerTraversal.py

This file provides type hints and interface definitions for classes in core/mac/RSHigherLayerTraversal.py.
Generated in WRS build environment.
"""

from typing import Dict, List, Tuple, Any, Optional, Union

class CTraversalItem:
    """
    CTraversalItem class for WRS automation.
    """

    controlName: Optional[Any]

    controlID: Optional[Any]

    level: Optional[Any]

    product: Optional[Any]

    ProcessID: Optional[Any]

    order: Optional[Any]

    fromControl: Optional[Any]

    father: Optional[Any]

    def __init__(self: Any) -> Any: ...

    def fromDataFrameRow(self: Any, row: pd.Series, allDf: pd.DataFrame) -> Any: ...

    def ToSequence(self: Any) -> list: ...

class CRSHigherLayerTraversal:
    """
    CRSHigherLayerTraversal class for WRS automation.
    """

    def __init__(self: Any, dbConnection: Any) -> Any: ...

    def _TraversalItem(self: Any, index: Any, item: CTraversalItem) -> Any: ...

    def _TraversalRow(self: Any, index: Any, row: Any, df: pd.DataFrame) -> Any: ...

    def _dataframeToTraversedItem(self: Any, df: pd.DataFrame) -> Any: ...

    def TraversalHighLaysers(self: Any, layer: Any = ...) -> Any: ...

    def TraversalLayer(self: Any, df: pd.DataFrame, layer: Any) -> Any: ...
