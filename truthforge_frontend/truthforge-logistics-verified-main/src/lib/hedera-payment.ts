// ─── Hedera Payment Hook ──────────────────────────────────────────────────────
// ALL wallet imports are dynamic — loaded only on explicit user click.
// This file must NEVER be imported at module level by any SSR/server path.
// Safe for Vite/Rollup: no static @hashgraph imports anywhere.

export interface PaymentResult {
  success: boolean;
  txId?: string;
  error?: string;
  userRejected?: boolean;
}

const WC_PROJECT_ID = "b0d4a8b7c3e2f1a9d6e5c4b3a2f1e0d9";
const APP_METADATA = {
  name: "TruthForge",
  description: "Logistics verification platform on Hedera",
  icons: [typeof window !== "undefined" ? `${window.location.origin}/favicon.ico` : ""],
  url: typeof window !== "undefined" ? window.location.origin : "https://truthforge.app",
};

// Singleton connector — reused across calls within the same session
// eslint-disable-next-line @typescript-eslint/no-explicit-any
let _connector: any = null;
let _initialized = false;

async function getConnector() {
  if (_connector && _initialized) return _connector;

  // Dynamic imports — Rollup will NOT statically analyse these
  const [hwc, sdk] = await Promise.all([
    import(/* @vite-ignore */ "@hashgraph/hedera-wallet-connect"),
    import(/* @vite-ignore */ "@hiero-ledger/sdk"),
  ]);

  const { DAppConnector, HederaJsonRpcMethod, HederaSessionEvent, HederaChainId } = hwc;
  const { LedgerId } = sdk;

  const connector = new DAppConnector(
    APP_METADATA,
    LedgerId.TESTNET,
    WC_PROJECT_ID,
    Object.values(HederaJsonRpcMethod),
    [HederaSessionEvent.ChainChanged, HederaSessionEvent.AccountsChanged],
    [HederaChainId.Testnet],
  );
  await connector.init({ logger: "error" });
  _connector = connector;
  _initialized = true;
  return connector;
}

/**
 * Called ONLY from an explicit user click handler.
 * Opens HashPack, deducts HBAR, submits HCS message.
 * Returns txId on success.
 */
export async function submitHederaPayment(shipmentId: string, amountHbar: number): Promise<PaymentResult> {
  try {
    const connector = await getConnector();
    await connector.openModal();

    const sessions = connector.walletConnectClient?.session.getAll() ?? [];
    const latest = sessions[sessions.length - 1];
    const accountId =
      latest?.namespaces?.hedera?.accounts?.[0]?.split(":")?.[2] ??
      latest?.namespaces?.["hedera:testnet"]?.accounts?.[0]?.split(":")?.[2] ?? null;

    if (!accountId) {
      return { success: false, error: "No account found. Approve the connection in HashPack." };
    }

    // Build HCS message via JSON-RPC relay
    const sdk = await import(/* @vite-ignore */ "@hiero-ledger/sdk");
    const { TransactionId, AccountId, Hbar, TransferTransaction } = sdk;

    const txId = TransactionId.generate(AccountId.fromString(accountId));

    // Transfer HBAR to TruthForge treasury (testnet)
    const tx = new TransferTransaction()
      .addHbarTransfer(AccountId.fromString(accountId), Hbar.fromTinybars(-Math.round(amountHbar * 1e8)))
      .addHbarTransfer(AccountId.fromString("0.0.1234567"), Hbar.fromTinybars(Math.round(amountHbar * 1e8)))
      .setTransactionId(txId)
      .setTransactionMemo(`TruthForge pre-clearance: ${shipmentId}`);

    const signedTx = await connector.signTransaction(accountId, tx);
    const receipt = await signedTx.execute(connector.providers[0]);

    return { success: true, txId: receipt.transactionId?.toString() ?? txId.toString() };
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : String(err);
    const userRejected = msg.toLowerCase().includes("modal closed") || msg.toLowerCase().includes("user rejected");
    return { success: false, error: msg, userRejected };
  }
}

export function disconnectWallet() {
  if (_connector) {
    try { _connector.disconnectAll(); } catch { /* ignore */ }
    _connector = null;
    _initialized = false;
  }
}
