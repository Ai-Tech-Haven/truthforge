"""
WooCommerce Order Webhook Handler

This module handles incoming webhooks from WooCommerce stores,
triggering verification workflows for new orders.
"""
import hmac
import hashlib
import json
import logging
import os
from flask import Blueprint, request, jsonify
from datetime import datetime, timezone

webhook_bp = Blueprint('webhook', __name__)
logger = logging.getLogger(__name__)


@webhook_bp.route('/webhook/woocommerce/order', methods=['POST'])
def handle_order_webhook():
    """
    Handle WooCommerce order webhook
    
    Receives order notifications from WooCommerce store and triggers
    the verification workflow through the orchestrator agent.
    """
    try:
        # Verify signature (skip in mock mode)
        signature = request.headers.get('X-WC-Webhook-Signature')
        payload = request.get_data(as_text=True)
        
        if not verify_webhook(payload, signature):
            logger.warning("Invalid webhook signature")
            return jsonify({"error": "Invalid signature"}), 401
        
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data received"}), 400
        
        order_id = data.get('id')
        order_status = data.get('status')
        logger.info(f"📦 Webhook: Order {order_id} status: {order_status}")
        
        # Trigger verification (import here to avoid circular imports)
        from flask import current_app
        orchestrator = current_app.config.get('ORCHESTRATOR')
        
        if orchestrator:
            result = orchestrator.process_request({
                'action': 'verify_order',
                'order_id': str(order_id),
                'order_data': data,
                'source': 'woocommerce',
                'timestamp': datetime.now(timezone.utc).isoformat()
            })
            
            verification_id = result.get('request_id') or result.get('verification_id')
        else:
            logger.warning("Orchestrator not available, webhook received but not processed")
            verification_id = None
        
        return jsonify({
            "received": True,
            "order_id": order_id,
            "verification_id": verification_id,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }), 200
    
    except Exception as e:
        logger.error(f"Error processing webhook: {e}", exc_info=True)
        # Return 200 to prevent webhook retries
        return jsonify({
            "received": True,
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }), 200


def verify_webhook(payload: str, signature: str) -> bool:
    """
    Verify WooCommerce webhook signature
    
    Args:
        payload: Raw request payload
        signature: X-WC-Webhook-Signature header value
        
    Returns:
        bool: True if signature is valid or in mock mode
    """
    # Skip verification in mock mode
    if os.getenv('MOCK_MODE', 'true').lower() == 'true':
        return True
    
    if not signature:
        return False
    
    secret = os.getenv('WOOCOMMERCE_WEBHOOK_SECRET', '')
    if not secret:
        logger.warning("WOOCOMMERCE_WEBHOOK_SECRET not set, skipping verification")
        return True
    
    expected = hmac.new(
        secret.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(signature, expected)
