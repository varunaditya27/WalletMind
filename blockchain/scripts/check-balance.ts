import hre from "hardhat";
import { formatEther } from "viem";

/**
 * Script to check account balances across all networks
 */
async function main() {
  console.log("\n💰 Checking Account Balances\n");
  console.log("=" .repeat(60));

  const networks = ["sepolia", "polygonAmoy", "baseSepolia"];
  
  for (const network of networks) {
    console.log(`\n🌐 Network: ${network.toUpperCase()}`);
    
    try {
      // Change network
      if (hre.network.name !== network) {
        console.log(`   ⏩ Switching to ${network}...`);
      }

      const [deployer] = await hre.viem.getWalletClients();
      const publicClient = await hre.viem.getPublicClient();
      
      console.log(`   📍 Address: ${deployer.account.address}`);
      
      // Get balance
      const balance = await publicClient.getBalance({ 
        address: deployer.account.address 
      });
      
      console.log(`   💵 Balance: ${formatEther(balance)} ETH`);
      
      // Status check
      const minBalance = network === "polygonAmoy" ? "0.1" : "0.05";
      if (parseFloat(formatEther(balance)) < parseFloat(minBalance)) {
        console.log(`   ⚠️  Warning: Balance below ${minBalance} ETH`);
        console.log(`   💡 Run: npm run testnet:fund`);
      } else {
        console.log(`   ✅ Sufficient balance for deployment`);
      }
      
    } catch (error: any) {
      console.log(`   ❌ Error: ${error.message}`);
      console.log(`   💡 Check your RPC URL in .env or hardhat.config.ts`);
    }
  }

  console.log("\n" + "=".repeat(60));
  console.log("\n💡 To fund accounts, run: npm run testnet:fund");
  console.log("📝 To deploy contracts, run: npm run deploy:<network>\n");
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error("\n❌ Check failed:");
    console.error(error);
    process.exit(1);
  });
