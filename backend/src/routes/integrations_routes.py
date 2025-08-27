# /home/ubuntu/grantthrive-platform/backend/src/routes/integrations_routes.py

from flask import Blueprint, request, jsonify
from datetime import datetime
from ..integrations.hubspot_api import HubSpotConnector
from ..integrations.salesforce_api import SalesforceConnector
from ..integrations.quickbooks_api import QuickBooksConnector
from ..integrations.myob_api import MYOBConnector
from ..integrations.xero_api import XeroConnector
from ..integrations.technologyone_api import TechnologyOneConnector

integrations_bp = Blueprint('integrations_bp', __name__)

# HubSpot Integration Endpoints
@integrations_bp.route('/integrations/hubspot/sync', methods=['POST'])
def sync_hubspot_contact():
    """
    API endpoint to sync a contact with HubSpot.
    Expects JSON payload with contact details.
    """
    data = request.get_json()

    if not data or 'email' not in data:
        return jsonify({"status": "error", "message": "Missing contact data or email."}), 400

    hubspot = HubSpotConnector()
    success, message = hubspot.sync_contact(data)

    if success:
        return jsonify({"status": "success", "message": message}), 200
    else:
        return jsonify({"status": "error", "message": message}), 500

# Salesforce Integration Endpoints
@integrations_bp.route('/integrations/salesforce/sync-opportunity', methods=['POST'])
def sync_salesforce_opportunity():
    """
    API endpoint to sync grant application as Salesforce opportunity.
    """
    data = request.get_json()

    if not data or 'grant_title' not in data:
        return jsonify({"status": "error", "message": "Missing grant data."}), 400

    salesforce = SalesforceConnector()
    success, message = salesforce.sync_opportunity(data)

    if success:
        return jsonify({"status": "success", "message": message}), 200
    else:
        return jsonify({"status": "error", "message": message}), 500

@integrations_bp.route('/integrations/salesforce/sync-contact', methods=['POST'])
def sync_salesforce_contact():
    """
    API endpoint to sync contact with Salesforce.
    """
    data = request.get_json()

    if not data or 'email' not in data:
        return jsonify({"status": "error", "message": "Missing contact data."}), 400

    salesforce = SalesforceConnector()
    success, message = salesforce.sync_contact(data)

    if success:
        return jsonify({"status": "success", "message": message}), 200
    else:
        return jsonify({"status": "error", "message": message}), 500

# QuickBooks Integration Endpoints
@integrations_bp.route('/integrations/quickbooks/sync-budget', methods=['POST'])
def sync_quickbooks_budget():
    """
    API endpoint to sync grant budget with QuickBooks.
    """
    data = request.get_json()

    if not data or 'funding_amount' not in data:
        return jsonify({"status": "error", "message": "Missing grant budget data."}), 400

    quickbooks = QuickBooksConnector()
    success, message = quickbooks.sync_grant_budget(data)

    if success:
        return jsonify({"status": "success", "message": message}), 200
    else:
        return jsonify({"status": "error", "message": message}), 500

@integrations_bp.route('/integrations/quickbooks/financial-report', methods=['GET'])
def get_quickbooks_report():
    """
    API endpoint to generate QuickBooks financial report.
    """
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    if not start_date or not end_date:
        return jsonify({"status": "error", "message": "Missing date parameters."}), 400

    quickbooks = QuickBooksConnector()
    success, report_data = quickbooks.get_financial_report(start_date, end_date)

    if success:
        return jsonify({"status": "success", "data": report_data}), 200
    else:
        return jsonify({"status": "error", "message": report_data}), 500

# MYOB Integration Endpoints
@integrations_bp.route('/integrations/myob/sync-financials', methods=['POST'])
def sync_myob_financials():
    """
    API endpoint to sync grant financials with MYOB.
    """
    data = request.get_json()

    if not data or 'funding_amount' not in data:
        return jsonify({"status": "error", "message": "Missing grant financial data."}), 400

    myob = MYOBConnector()
    success, sync_summary = myob.sync_grant_financials(data)

    if success:
        return jsonify({"status": "success", "data": sync_summary}), 200
    else:
        return jsonify({"status": "error", "message": sync_summary}), 500

@integrations_bp.route('/integrations/myob/grant-report', methods=['GET'])
def get_myob_grant_report():
    """
    API endpoint to generate MYOB grant report.
    """
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    if not start_date or not end_date:
        return jsonify({"status": "error", "message": "Missing date parameters."}), 400

    myob = MYOBConnector()
    success, report_data = myob.generate_grant_report(start_date, end_date)

    if success:
        return jsonify({"status": "success", "data": report_data}), 200
    else:
        return jsonify({"status": "error", "message": report_data}), 500

# Xero Integration Endpoints
@integrations_bp.route('/integrations/xero/sync-grant', methods=['POST'])
def sync_xero_grant():
    """
    API endpoint to sync complete grant with Xero.
    """
    data = request.get_json()

    if not data or 'funding_amount' not in data:
        return jsonify({"status": "error", "message": "Missing grant data."}), 400

    xero = XeroConnector()
    success, sync_summary = xero.sync_complete_grant(data)

    if success:
        return jsonify({"status": "success", "data": sync_summary}), 200
    else:
        return jsonify({"status": "error", "message": sync_summary}), 500

@integrations_bp.route('/integrations/xero/financial-report', methods=['GET'])
def get_xero_financial_report():
    """
    API endpoint to generate Xero financial report.
    """
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    if not start_date or not end_date:
        return jsonify({"status": "error", "message": "Missing date parameters."}), 400

    xero = XeroConnector()
    success, report_data = xero.generate_financial_report(start_date, end_date)

    if success:
        return jsonify({"status": "success", "data": report_data}), 200
    else:
        return jsonify({"status": "error", "message": report_data}), 500

# TechnologyOne Integration Endpoints
@integrations_bp.route('/integrations/technologyone/sync-lifecycle', methods=['POST'])
def sync_technologyone_lifecycle():
    """
    API endpoint to sync complete grant lifecycle with TechnologyOne.
    """
    data = request.get_json()

    if not data or 'grant_id' not in data:
        return jsonify({"status": "error", "message": "Missing grant lifecycle data."}), 400

    t1 = TechnologyOneConnector()
    success, sync_summary = t1.sync_complete_grant_lifecycle(data)

    if success:
        return jsonify({"status": "success", "data": sync_summary}), 200
    else:
        return jsonify({"status": "error", "message": sync_summary}), 500

@integrations_bp.route('/integrations/technologyone/compliance-report', methods=['GET'])
def get_technologyone_compliance_report():
    """
    API endpoint to generate TechnologyOne compliance report.
    """
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    if not start_date or not end_date:
        return jsonify({"status": "error", "message": "Missing date parameters."}), 400

    t1 = TechnologyOneConnector()
    success, report_data = t1.generate_compliance_report(start_date, end_date)

    if success:
        return jsonify({"status": "success", "data": report_data}), 200
    else:
        return jsonify({"status": "error", "message": report_data}), 500

# General Integration Status Endpoint
@integrations_bp.route('/integrations/status', methods=['GET'])
def get_integrations_status():
    """
    API endpoint to check status of all integrations.
    """
    status_results = {}
    
    # Test each integration
    integrations = [
        ('hubspot', HubSpotConnector),
        ('salesforce', SalesforceConnector),
        ('quickbooks', QuickBooksConnector),
        ('myob', MYOBConnector),
        ('xero', XeroConnector),
        ('technologyone', TechnologyOneConnector)
    ]
    
    for name, connector_class in integrations:
        try:
            connector = connector_class()
            # Test authentication
            auth_success, auth_message = connector.authenticate()
            status_results[name] = {
                'status': 'connected' if auth_success else 'disconnected',
                'message': auth_message,
                'last_checked': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        except Exception as e:
            status_results[name] = {
                'status': 'error',
                'message': str(e),
                'last_checked': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
    
    return jsonify({"status": "success", "integrations": status_results}), 200

