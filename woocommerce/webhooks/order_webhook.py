"""
WooCommerce Order Webhook Handler

Handles incoming WooCommerce webhooks with HMAC-SHA256 signature
verification using the secret from WOOCOMMERCE_WEBHOOK_SECRET in .env.
"""
import hmac
import hashlib
import base64
import logging
import os
from flask import Blueprint, request, jsonify
from datetime import datetime, timezone

webhook_bp = Blueprint('webhook', __name__)
logger = logging.getLogger(__name__)


def verify_webhook(payload: bytes, signature: str) -> bool:
    """
    Verify WooCommerce webhook HMAC-SHA256 signature.

    WooCommerce signs the raw payload with the webhook secret using
    HMAC-SHA256 and base64-encodes the result, sending it in the
    X-WC-Webhook-Signature header.

    Args:
        payload: Raw request body bytes
        signature: Value of X-WC-Webhook-Signature header

    Returns:
        bool: True if valid, or if verification is skipped
    """
    # Always pass in mock mode
    if os.getenv('MOCK_MODE', 'true').lower() == 'true':
        return True

    secret = os.getenv('WOOCOMMERCE_WEBHOOK_SECRET', '')
    if not secret:
        logger.warning("WOOCOMMERCE_WEBHOOK_SECRET not set â€” skipping verification")
        return True

    if not signature:
        logger.warning("No X-WC-Webhook-Signature header provided")
        return False

    try:
        computed = base64.b64encode(
            hmac.new(
                secret.encode('utf-8'),
                payload,
                hashlib.sha256
            ).digest()
        ).decode('utf-8')
        return hmac.compare_digest(computed, signature)
    except Exception as e:
        logger.error(f"Webhook signature verification error: {e}")
        return False


@webhook_bp.route('/webhook/woocommerce/order', methods=['POST'])
def handle_order_webhook():
    """
    Handle incoming WooCommerce order webhook.

    Verifies the HMAC-SHA256 signature, parses the order payload,
    and routes it through the TruthForge orchestrator for verification.
    Returns 200 even on processing errors to prevent WooCommerce retries.
    """
    # Read raw bytes for signature verification (must be before get_json)
    payload_bytes = request.get_data()
    signature = request.headers.get('X-WC-Webhook-Signature', '')

    # Verify signature in live mode
    if not verify_webhook(payload_bytes, signature):
        logger.warning(f"Invalid webhook signature received â€” rejecting request")
        return jsonify({"error": "Invalid signature"}), 401

    # Parse JSON body
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "No JSON payload received"}), 400

    order_id = data.get('id')
    order_status = data.get('status')
    logger.info(f"Verified WooCommerce webhook: Order {order_id}, status={order_status}")

    try:
        # Use the orchestrator injected into Flask app config
        from flask import current_app
        orchestrator = current_app.config.get('ORCHESTRATOR')

        verification_id = None
        if orchestrator:
            result = orchestrator.process_request({
                'action': 'verify_order',
                'order_id': str(order_id),
                'order_data': data,
                'source': 'woocommerce',
                'timestamp': datetime.now(timezone.utc).isoformat()
            })
            verification_id = result.get('request_id') or result.get('verification_id')
            logger.info(f"Order {order_id} queued for verification: {verification_id}")
        else:
            logger.warning("Orchestrator not available â€” webhook received but not processed")

        return jsonify({
            "received": True,
            "order_id": order_id,
            "status": order_status,
            "verification_id": verification_id,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }), 200

    except Exception as e:
        logger.error(f"Error processing webhook for order {order_id}: {e}", exc_info=True)
        # Return 200 to prevent WooCommerce from retrying
        return jsonify({
            "received": True,
            "order_id": order_id,
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }), 200
