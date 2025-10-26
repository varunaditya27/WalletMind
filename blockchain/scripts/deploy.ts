import hre from "hardhat";
import { parseEther, formatEther } from "viem";
import { writeFileSync } from "fs";
import { join } from "path";

/**
 * Deployment script for WalletMind smart contracts
 * 
 * Deploys AgentWallet and AgentRegistry to specified network
 * and saves contract addresses to deployed-contracts.json
 */
async function main() {
  console.log(`\n🚀 Deploying WalletMind contracts...`);

  // Connect to network and get viem
  const { viem } = await hre.network.connect();
  
  // Get deployer account
  const [deployer] = await viem.getWalletClients();
  const publicClient = await viem.getPublicClient();
  
  // Get network from chain ID
  const chainId = publicClient.chain.id;
  const networkMap: Record<number, string> = {
    1: "mainnet",
    11155111: "sepolia",
    31337: "hardhat",
  };
  const network = networkMap[chainId] || `chain-${chainId}`;
  
  console.log(`📡 Network: ${network} (Chain ID: ${chainId})`);
  console.log(`📝 Deployer address: ${deployer.account.address}`);
  
  // Check balance
  const balance = await publicClient.getBalance({ 
    address: deployer.account.address 
  });
  console.log(`💰 Deployer balance: ${formatEther(balance)} ETH`);
  
  if (balance < parseEther("0.01")) {
    console.warn("⚠️  Warning: Low balance. You may need to fund your account.");
  }

  // Deploy contracts directly with viem (simpler than ignition for basic deploys)
  console.log("\n📦 Deploying contracts...");
  
  console.log("   Deploying AgentWallet...");
  const agentWallet = await viem.deployContract("AgentWallet", 
    [deployer.account.address, deployer.account.address] as any
  );
  
  console.log("   Deploying AgentRegistry...");
  const agentRegistry = await viem.deployContract("AgentRegistry",
    [deployer.account.address] as any
  );

  console.log(`\n✅ Deployment complete!`);
  console.log(`   AgentWallet: ${agentWallet.address}`);
  console.log(`   AgentRegistry: ${agentRegistry.address}`);

  // Save deployment info to root deployed-contracts.json
  const deploymentInfo = {
    network,
    chainId: publicClient.chain.id,
    deployer: deployer.account.address,
    timestamp: new Date().toISOString(),
    blockNumber: await publicClient.getBlockNumber(),
    contracts: {
      AgentWallet: agentWallet.address,
      AgentRegistry: agentRegistry.address,
    },
  };

  // Read existing deployments
  let allDeployments: any = {};
  try {
    const existingData = require("../../deployed-contracts.json");
    allDeployments = existingData;
  } catch (error) {
    // File doesn't exist or is empty
  }

  // Update with new deployment
  allDeployments[network] = deploymentInfo;

  // Write to root directory
  const rootPath = join(__dirname, "../../deployed-contracts.json");
  writeFileSync(rootPath, JSON.stringify(allDeployments, null, 2));
  
  console.log(`\n📄 Deployment info saved to deployed-contracts.json`);

  // Fund AgentWallet with small amount for testing
  if (network.includes("local") || network.includes("hardhat")) {
    console.log("\n💸 Funding AgentWallet for local testing...");
    await deployer.sendTransaction({
      to: agentWallet.address,
      value: parseEther("0.1"),
    });
    console.log("   Sent 0.1 ETH to AgentWallet");
  }

  // Verify on Etherscan (if on testnet/mainnet)
  if (!network.includes("local") && !network.includes("hardhat")) {
    console.log("\n🔍 To verify contracts on Etherscan, run:");
    console.log(`   npx hardhat verify --network ${network} ${agentWallet.address}`);
    console.log(`   npx hardhat verify --network ${network} ${agentRegistry.address}`);
  }

  console.log("\n🎉 Deployment successful!\n");
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error("\n❌ Deployment failed:");
    console.error(error);
    process.exit(1);
  });
