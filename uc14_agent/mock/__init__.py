"""
UC14 GL Anomaly Detection Agent — Mock SAP S/4HANA & ERP Services
Provides mock data and mock SAP REST/RFC interfaces for BTP Cloud Foundry testing.
"""
from mock.mock_data import get_mock_postings, get_mock_baselines, get_mock_bank_entries, get_mock_data, reset_mock_data
from mock.mock_sap_service import MockSAPService

mock_sap_service = MockSAPService()

__all__ = [
    "get_mock_postings",
    "get_mock_baselines",
    "get_mock_bank_entries",
    "get_mock_data",
    "reset_mock_data",
    "mock_sap_service",
    "MockSAPService",
]
