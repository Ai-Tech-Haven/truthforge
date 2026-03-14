const { Client, TopicCreateTransaction, PrivateKey } = require("@hashgraph/sdk");

async function main() {
  // Your Hedera credentials
  const accountId = "0.0.7974354";
  const privateKey = "3030020100300706052b8104000a04220420f2898f6397f83bf1eb38da89a735325aba3a50aa26601dcd62e0f7ff3261a39a";

  // Create client for testnet
  const client = Client.forTestnet();
  client.setOperator(accountId, PrivateKey.fromStringDer(privateKey));

  console.log("Creating Hedera topic...");
  console.log(`Using account: ${accountId}`);

  try {
    const txResponse = await new TopicCreateTransaction()
      .setTopicMemo("TruthForge Verification Logs")
      .execute(client);

    const { topicId } = await txResponse.getReceipt(client);

    console.log("\n✅ SUCCESS!");
    console.log(`\nTopic ID: ${topicId.toString()}`);
    console.log("\nAdd this to your .env file:");
    console.log(`HCS_TOPIC_ID=${topicId.toString()}`);
    console.log(`HEDERA_ACCOUNT_ID=${accountId}`);
    console.log(`HEDERA_PRIVATE_KEY=${privateKey}`);

  } catch (error) {
    console.error("\n❌ ERROR:", error.message);
    process.exit(1);
  } finally {
    client.close();
  }
}

main();
