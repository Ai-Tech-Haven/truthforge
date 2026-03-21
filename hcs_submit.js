#!/usr/bin/env node
/**
 * TruthForge HCS Submission Script
 * Called by Python HederaClient via subprocess.
 * Reads JSON message from stdin, submits to Hedera Consensus Service,
 * prints transaction ID to stdout.
 *
 * Usage:
 *   echo '{"message":"...","topicId":"0.0.8109600"}' | node hcs_submit.js
 *
 * Env vars required:
 *   HEDERA_ACCOUNT_ID, HEDERA_PRIVATE_KEY, HEDERA_NETWORK (optional, default: testnet)
 */

const { Client, TopicMessageSubmitTransaction, PrivateKey } = require('@hashgraph/sdk');

async function main() {
  // Read JSON from stdin
  let raw = '';
  for await (const chunk of process.stdin) raw += chunk;

  let input;
  try {
    input = JSON.parse(raw);
  } catch (e) {
    process.stderr.write(`[hcs_submit] Invalid JSON input: ${e.message}\n`);
    process.exit(1);
  }

  const accountId = process.env.HEDERA_ACCOUNT_ID;
  const privateKeyStr = process.env.HEDERA_PRIVATE_KEY;
  const network = (process.env.HEDERA_NETWORK || 'testnet').toLowerCase();
  const topicId = input.topicId || process.env.HCS_TOPIC_ID;
  const message = input.message || '';

  if (!accountId || !privateKeyStr) {
    process.stderr.write('[hcs_submit] HEDERA_ACCOUNT_ID and HEDERA_PRIVATE_KEY are required\n');
    process.exit(1);
  }
  if (!topicId) {
    process.stderr.write('[hcs_submit] topicId is required\n');
    process.exit(1);
  }

  let client;
  try {
    const privateKey = PrivateKey.fromStringDer(privateKeyStr);
    client = network === 'mainnet' ? Client.forMainnet() : Client.forTestnet();
    client.setOperator(accountId, privateKey);
    client.setRequestTimeout(30000);
  } catch (e) {
    process.stderr.write(`[hcs_submit] Client init error: ${e.message}\n`);
    process.exit(1);
  }

  try {
    const txResponse = await new TopicMessageSubmitTransaction()
      .setTopicId(topicId)
      .setMessage(message)
      .execute(client);

    const receipt = await txResponse.getReceipt(client);
    const txId = txResponse.transactionId.toString();
    const seqNum = receipt.topicSequenceNumber
      ? receipt.topicSequenceNumber.toString()
      : null;

    // Output result as JSON to stdout — Python reads this
    process.stdout.write(JSON.stringify({
      success: true,
      transactionId: txId,
      topicSequenceNumber: seqNum,
      topicId: topicId,
      network: network,
    }) + '\n');

  } catch (e) {
    process.stderr.write(`[hcs_submit] Submission error: ${e.message}\n`);
    // Output failure JSON so Python can handle gracefully
    process.stdout.write(JSON.stringify({
      success: false,
      error: e.message,
      topicId: topicId,
    }) + '\n');
    process.exit(1);
  } finally {
    client.close();
  }
}

main().catch(e => {
  process.stderr.write(`[hcs_submit] Fatal: ${e.message}\n`);
  process.exit(1);
});
