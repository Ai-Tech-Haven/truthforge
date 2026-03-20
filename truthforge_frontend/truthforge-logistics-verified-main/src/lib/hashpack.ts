// hashpack.ts — Singleton DAppConnector for HashPack wallet
// Client-only. Never imported at SSR/build time from top-level.
// All wallet SDK code lives here — nowhere else.

import {
  DAppConnector,
  HederaJsonRpcMethod,
  HederaSessionEvent,
  HederaChainId,
} from "@hashgraph/hedera-wallet-connect";
import { LedgerId } from "@hiero-ledger/sdk";

const WC_PROJECT_ID = "b0d4a8b7c3e2f1a9d6e5c4b3a2f1e0d9";

let _connector: DAppConnector | null = null;
let _initialized = false;

export async function getConnector(): Promise<DAppConnector> {
  if (_connector && _initialized) return _connector;

  const meta = {
    name: "TruthForge",
    description: "Verifiable Trade & Logistics Proof",
    icons: [typeof window !== "undefined" ? `${window.location.origin}/favicon.ico` : ""],
    url: typeof window !== "undefined" ? window.location.origin : "",
  };

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

export function resetConnector() {
  try { _connector?.disconnectAll?.(); } catch { /* ignore */ }
  _connector = null;
  _initialized = false;
}
