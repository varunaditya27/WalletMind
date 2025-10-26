import hre from "hardhat";
import { formatEther } from "viem";

/**
 * Script to interact with AgentRegistry contract
 * 
 * Demonstrates:
 * - Agent registration (FR-012)
 * - Service offerings
 * - Reputation management
 * - Agent discovery
 */
async function main() {
  const network = hre.network.name;
  console.log(`\n🤖 Interacting with AgentRegistry on ${network}...\n`);

  // Load deployment info
  const deployments = require("../../deployed-contracts.json");
  const deployment = deployments[network];
  
  if (!deployment) {
    throw new Error(`No deployment found for network: ${network}`);
  }

  const registryAddress = deployment.contracts.AgentRegistry;
  console.log(`📍 AgentRegistry address: ${registryAddress}`);

  // Get contract instance
  const registry = await hre.viem.getContractAt(
    "AgentRegistry",
    registryAddress
  );

  const [, agent1, agent2] = await hre.viem.getWalletClients();
  const publicClient = await hre.viem.getPublicClient();

  // Example 1: Register agents (FR-012)
  console.log("📝 Example 1: Registering AI agents...");
  
  const agent1Metadata = JSON.stringify({
    name: "DataAnalyzer AI",
    capabilities: ["data_analysis", "api_integration"],
    version: "1.0.0",
    contact: "agent1@walletmind.ai",
  });
  
  const agent2Metadata = JSON.stringify({
    name: "PaymentProcessor AI",
    capabilities: ["payment_processing", "transaction_verification"],
    version: "1.0.0",
    contact: "agent2@walletmind.ai",
  });

  const reg1Hash = await registry.write.registerAgent(
    [agent1Metadata],
    { account: agent1.account }
  );
  await publicClient.waitForTransactionReceipt({ hash: reg1Hash });
  console.log(`   ✅ Agent 1 registered: ${agent1.account.address}`);

  const reg2Hash = await registry.write.registerAgent(
    [agent2Metadata],
    { account: agent2.account }
  );
  await publicClient.waitForTransactionReceipt({ hash: reg2Hash });
  console.log(`   ✅ Agent 2 registered: ${agent2.account.address}\n`);

  // Example 2: Register services
  console.log("💼 Example 2: Registering services...");
  
  const serviceHash = await registry.write.registerService(
    ["data_analysis", 1000000000000000n, "AI-powered data analysis service"],
    { account: agent1.account }
  );
  await publicClient.waitForTransactionReceipt({ hash: serviceHash });
  console.log(`   ✅ Service registered by Agent 1\n`);

  // Example 3: Query agent info
  console.log("🔍 Example 3: Querying agent information...");
  
  const agent1Info = await registry.read.getAgent([agent1.account.address]);
  console.log(`   Agent 1:`);
  console.log(`     - Reputation: ${agent1Info.reputation}`);
  console.log(`     - Transaction count: ${agent1Info.transactionCount}`);
  console.log(`     - Active: ${agent1Info.active}`);
  console.log(`     - Services: ${agent1Info.services.length}\n`);

  // Example 4: Update reputation
  console.log("⭐ Example 4: Simulating reputation updates...");
  
  // Simulate successful transactions
  for (let i = 0; i < 5; i++) {
    await registry.write.updateReputation([agent1.account.address, true]);
  }
  
  const updatedInfo = await registry.read.getAgent([agent1.account.address]);
  console.log(`   Agent 1 new reputation: ${updatedInfo.reputation}`);
  console.log(`   Success rate: ${await registry.read.getSuccessRate([agent1.account.address])}%\n`);

  // Example 5: Agent discovery
  console.log("🌐 Example 5: Agent discovery...");
  
  const allAgents = await registry.read.getAllAgents();
  console.log(`   Total registered agents: ${allAgents.length}`);
  
  const activeAgents = await registry.read.getActiveAgents();
  console.log(`   Active agents: ${activeAgents.length}`);
  
  for (const agentAddr of activeAgents) {
    const info = await registry.read.getAgent([agentAddr]);
    console.log(`     - ${agentAddr}: Reputation ${info.reputation}`);
  }

  // Example 6: Service query
  console.log("\n🔧 Example 6: Querying services...");
  
  const service = await registry.read.getService([agent1.account.address, "data_analysis"]);
  console.log(`   Service: ${service.serviceId}`);
  console.log(`   Provider: ${service.provider}`);
  console.log(`   Price: ${formatEther(service.price)} ETH`);
  console.log(`   Available: ${service.available}`);

  console.log("\n✨ Interaction complete!\n");
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error("\n❌ Interaction failed:");
    console.error(error);
    process.exit(1);
  });
