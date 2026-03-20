// hedera-payment.ts — Frontend payment delegation
// Frontend does NOT sign transactions or use @hashgraph/sdk.
// All Hedera logic (HCS, HBAR transfer, pre-clearance) runs on the Railway backend.
// Frontend sends: { accountId, shipmentId, mode, amountHbar }
// Backend returns: { txId, hashscanUrl, status }

import { API_BASE } from "@/lib/api-client";

export interface PaymentResult {
  success: boolean;
  txId?: string;
  hashscanUrl?: string;
  error?: string;
  userRejected?: boolean;
}

/**
 * Delegates pre-clearance payment to the Railway backend.
 * Backend handles: HBAR transfer, HCS message, transaction signing.
 * Frontend only passes the connected wallet accountId as identity proof.
 */
export async function submitHederaPayment(
  shipmentId: string,
  amountHbar: number,
  accountId?: string | null,
): Promise<PaymentResult> {
  try {
    const res = await fetch(`${API_BASE}/api/v1/shipments/${shipmentId}/pre-clearance`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        shipmentId,
        amountHbar,
        accountId: accountId ?? null,
        network: "testnet",
      }),
      signal: AbortSignal.timeout(30000),
    });

    if (!res.ok) {
      const text = await res.text();
      return { success: false, error: `Backend error ${res.status}: ${text}` };
    }

    const data = await res.json() as {
      txId?: string;
      hashscanUrl?: string;
      status?: string;
      error?: string;
    };

    if (!data.txId) {
      return { success: false, error: data.error ?? "No transaction ID returned from backend." };
    }

    return {
      success: true,
      txId: data.txId,
      hashscanUrl: data.hashscanUrl ?? `https://hashscan.io/testnet/transaction/${data.txId}`,
    };
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : String(err);
    return { success: false, error: msg };
  }
}
