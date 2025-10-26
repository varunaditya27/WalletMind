import hre from "hardhat";
import { formatEther } from "viem";

/**
 * Script to check Sepolia account balance
 */
async function main() {
  console.log("\n💰 Checking Sepolia Account Balance\n");
  console.log("=" .repeat(60));

  console.log(`\n🌐 Network: ETHEREUM SEPOLIA TESTNET`);
  
  try {
    // Connect to network and get viem
    const { viem } = await hre.network.connect();
    
    const [deployer] = await viem.getWalletClients();
    const publicClient = await viem.getPublicClient();
    
    console.log(`   📍 Address: ${deployer.account.address}`);
    
    // Get balance
    const balance = await publicClient.getBalance({ 
      address: deployer.account.address 
    });
    
    console.log(`   💵 Balance: ${formatEther(balance)} ETH`);
    
    // Status check
    const minBalance = "0.05";
    if (parseFloat(formatEther(balance)) < parseFloat(minBalance)) {
      console.log(`   ⚠️  Warning: Balance below ${minBalance} ETH`);
      console.log(`   💡 Run: npm run testnet:fund`);
    } else {
      console.log(`   ✅ Sufficient balance for deployment`);
    }
    
    // Etherscan link
    console.log(`   🔍 View on Etherscan: https://sepolia.etherscan.io/address/${deployer.account.address}`);
    
  } catch (error: any) {
    console.log(`   ❌ Error: ${error.message}`);
    console.log(`   💡 Check your RPC URL and private key in .env`);
  }

  console.log("\n" + "=".repeat(60));
  console.log("\n💡 To fund your account, run: npm run testnet:fund");
  console.log("📝 To deploy contracts, run: npm run deploy:sepolia\n");
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error("\n❌ Check failed:");
    console.error(error);
    process.exit(1);
  });
