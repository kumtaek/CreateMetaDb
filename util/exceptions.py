# -*- coding: utf-8 -*-
"""
Custom Exceptions for the SourceAnalyzer project.
"""

class CircularReferenceError(Exception):
    """
    Exception raised when a circular reference is detected during MyBatis XML <include> processing.
    """
    def __init__(self, message, path=None):
        """
        Initializes the CircularReferenceError.

        Args:
            message (str): The error message.
            path (list, optional): The path that caused the circular reference. Defaults to None.
        """
        super().__init__(message)
        self.path = path or []
