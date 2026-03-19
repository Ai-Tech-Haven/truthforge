// ─── Hedera Payment ───────────────────────────────────────────────────────────
// VERCEL-SAFE: zero static imports of @hashgraph or @hiero-ledger.
// Module specifiers are assembled at runtime so Rollup never resolves them.
// All wallet logic runs client-side only, gated by typeof window check.

export interface PaymentResult {
  success: boolean;
  txId?: string;
  hashscanUrl?: string;
  error?: string;
  userRejected?: boolean;
}

// Runtime-assembled specifiers — Rollup cannot statically analyse these
const _hwc  = () => ["@hashgraph", "hedera-wallet-connect"].join("/");
const _sdk  = () => ["@hiero-ledger", "sdk"].join("/");

const WC_PROJECT_ID = "b0d4a8b7c3e2f1a9d6e5c4b3a2f1e0d9";

// eslint-disable-next-line @typescript-eslint/no-explicit-any
let _connector: any = null;
let _initialized = false;

async function getConnector() {
  if (typeof window === "undefined") throw new Error("Wallet unavailable server-side");
  if (_connector && _initialized) return _connector;

  const meta = {
    name: "TruthForge",
    description: "Logistics verification platform on Hedera",
    icons: [`${window.location.origin}/favicon.ico`],
    url: window.location.origin,
  };

  // Dynamic imports with runtime-built specifiers — invisible to Rollup
  const [hwc, sdk] = await Promise.all([
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    (Function("s", "return import(s)")(_hwc()) as Promise<any>),
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    (Function("s", "return import(s)")(_sdk()) as Promise<any>),
  ]);

  const { DAppConnector, HederaJsonRpcMethod, HederaSessionEvent, HederaChainId } = hwc;
  const { LedgerId } = sdk;

  const connector = new DAppConnector(
    meta,
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
 * Opens HashPack, deducts HBAR, submits HCS transaction.
 */
export async function submitHederaPayment(
  shipmentId: string,
  amountHbar: number,
): Promise<PaymentResult> {
  try {
    const connector = await getConnector();
    await connector.openModal();

    const sessions = connector.walletConnectClient?.session.getAll() ?? [];
    const latest = sessions[sessions.length - 1];
    const accountId =
      latest?.namespaces?.hedera?.accounts?.[0]?.split(":")?.[2] ??
      latest?.namespaces?.["hedera:testnet"]?.accounts?.[0]?.split(":")?.[2] ??
      null;

    if (!accountId) {
      return { success: false, error: "No account found. Approve the connection in HashPack." };
    }

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const sdk: any = await (Function("s", "return import(s)")(_sdk()));
    const { TransactionId, AccountId, Hbar, TransferTransaction } = sdk;

    const txId = TransactionId.generate(AccountId.fromString(accountId));
    const tinybars = Math.round(amountHbar * 1e8);

    const tx = new TransferTransaction()
      .addHbarTransfer(AccountId.fromString(accountId), Hbar.fromTinybars(-tinybars))
      .addHbarTransfer(AccountId.fromString("0.0.1234567"), Hbar.fromTinybars(tinybars))
      .setTransactionId(txId)
      .setTransactionMemo(`TruthForge pre-clearance: ${shipmentId}`);

    const signedTx = await connector.signTransaction(accountId, tx);
    const receipt = await signedTx.execute(connector.providers[0]);
    const finalTxId = receipt.transactionId?.toString() ?? txId.toString();

    return {
      success: true,
      txId: finalTxId,
      hashscanUrl: `https://hashscan.io/testnet/transaction/${finalTxId}`,
    };
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : String(err);
    const userRejected =
      msg.toLowerCase().includes("modal closed") ||
      msg.toLowerCase().includes("user rejected");
    return { success: false, error: msg, userRejected };
  }
}

export function disconnectWallet(): void {
  if (_connector) {
    try { _connector.disconnectAll(); } catch { /* ignore */ }
    _connector = null;
    _initialized = false;
  }
}
