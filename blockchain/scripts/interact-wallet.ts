import hre from "hardhat";
import { parseEther, formatEther } from "viem";

/**
 * Script to interact with deployed AgentWallet contract
 * 
 * Demonstrates:
 * - Logging AI decisions (FR-007)
 * - Executing verified transactions (FR-005, FR-007)
 * - Querying transaction history (FR-008)
 */
async function main() {
  const network = hre.network.name;
  console.log(`\n🤖 Interacting with AgentWallet on ${network}...\n`);

  // Load deployment info
  const deployments = require("../../deployed-contracts.json");
  const deployment = deployments[network];
  
  if (!deployment) {
    throw new Error(`No deployment found for network: ${network}`);
  }

  const agentWalletAddress = deployment.contracts.AgentWallet;
  console.log(`📍 AgentWallet address: ${agentWalletAddress}`);

  // Get contract instance
  const agentWallet = await hre.viem.getContractAt(
    "AgentWallet",
    agentWalletAddress
  );

  const [owner, agent, recipient] = await hre.viem.getWalletClients();
  const publicClient = await hre.viem.getPublicClient();

  // Check wallet balance
  const balance = await agentWallet.read.getBalance();
  console.log(`💰 Wallet balance: ${formatEther(balance)} ETH\n`);

  // Example 1: Log a decision (FR-007)
  console.log("📝 Example 1: Logging an AI decision...");
  const decisionData = JSON.stringify({
    intent: "Pay 0.01 ETH for API access",
    rationale: "Agent needs weather data for analysis",
    timestamp: Date.now(),
    confidence: 0.95,
  });
  
  const decisionHash = hre.viem.keccak256(hre.viem.toHex(decisionData));
  const ipfsCid = "QmExampleCID123"; // In production, upload to IPFS first
  
  const logHash = await agentWallet.write.logDecision(
    [decisionHash, ipfsCid],
    { account: agent.account }
  );
  
  await publicClient.waitForTransactionReceipt({ hash: logHash });
  console.log(`   ✅ Decision logged: ${decisionHash}`);
  console.log(`   📦 IPFS CID: ${ipfsCid}\n`);

  // Example 2: Execute the logged decision (FR-005)
  console.log("⚡ Example 2: Executing verified decision...");
  const amount = parseEther("0.01");
  
  const execHash = await agentWallet.write.verifyAndExecute(
    [decisionHash, recipient.account.address, amount],
    { account: owner.account }
  );
  
  await publicClient.waitForTransactionReceipt({ hash: execHash });
  console.log(`   ✅ Transaction executed: ${execHash}`);
  console.log(`   💸 Sent ${formatEther(amount)} ETH to ${recipient.account.address}\n`);

  // Example 3: Query transaction history (FR-008)
  console.log("📊 Example 3: Querying transaction history...");
  const txCount = await agentWallet.read.getTransactionCount();
  console.log(`   Total transactions: ${txCount}`);
  
  if (txCount > 0n) {
    const lastTx = await agentWallet.read.getTransaction([txCount - 1n]);
    console.log(`   Last transaction:`);
    console.log(`     - To: ${lastTx.to}`);
    console.log(`     - Value: ${formatEther(lastTx.value)} ETH`);
    console.log(`     - Category: ${lastTx.category}`);
    console.log(`     - Success: ${lastTx.success}`);
  }

  // Example 4: Check spending limits (NFR-005)
  console.log("\n💳 Example 4: Checking spending limits...");
  const limit = await agentWallet.read.spendingLimits(["0x0000000000000000000000000000000000000000"]);
  const spent = await agentWallet.read.totalSpent(["0x0000000000000000000000000000000000000000"]);
  console.log(`   Spending limit: ${formatEther(limit)} ETH`);
  console.log(`   Total spent: ${formatEther(spent)} ETH`);
  console.log(`   Remaining: ${formatEther(limit - spent)} ETH`);

  console.log("\n✨ Interaction complete!\n");
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error("\n❌ Interaction failed:");
    console.error(error);
    process.exit(1);
  });
