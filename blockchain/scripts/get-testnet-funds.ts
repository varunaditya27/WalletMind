import { parseEther } from "viem";

/**
 * Script to request testnet funds from faucets
 * 
 * Networks supported:
 * - Ethereum Sepolia
 * - Polygon Amoy
 * - Base Sepolia
 */
async function main() {
  console.log("\n💰 Testnet Faucet Information\n");
  console.log("=" .repeat(60));

  const account = process.env.SEPOLIA_PRIVATE_KEY 
    ? "0x" + process.env.SEPOLIA_PRIVATE_KEY.slice(0, 10) + "..." 
    : "Not configured";

  console.log(`\n📝 Your account: ${account}`);
  console.log("\n🚰 Faucets for Each Network:\n");

  console.log("1️⃣  ETHEREUM SEPOLIA");
  console.log("   Faucet URLs:");
  console.log("   - https://sepoliafaucet.com/");
  console.log("   - https://www.alchemy.com/faucets/ethereum-sepolia");
  console.log("   - https://cloud.google.com/application/web3/faucet/ethereum/sepolia");
  console.log("   Amount: 0.5 ETH per request");
  console.log("   Requirements: GitHub/Twitter account\n");

  console.log("2️⃣  POLYGON AMOY (Mumbai successor)");
  console.log("   Faucet URLs:");
  console.log("   - https://faucet.polygon.technology/");
  console.log("   - https://www.alchemy.com/faucets/polygon-amoy");
  console.log("   Amount: 0.5 MATIC per request");
  console.log("   Requirements: Alchemy account\n");

  console.log("3️⃣  BASE SEPOLIA");
  console.log("   Faucet URLs:");
  console.log("   - https://www.alchemy.com/faucets/base-sepolia");
  console.log("   - Get Sepolia ETH first, then bridge to Base");
  console.log("   Amount: 0.1 ETH per request");
  console.log("   Requirements: Alchemy account\n");

  console.log("=" .repeat(60));

  console.log("\n💡 Tips:");
  console.log("   1. Request from multiple faucets for more funds");
  console.log("   2. You need funds on ALL networks for full testing");
  console.log("   3. Keep some ETH for gas fees (~0.05 ETH recommended)");
  console.log("   4. Faucets usually have rate limits (1 request per 24h)");

  console.log("\n📋 Next Steps:");
  console.log("   1. Visit the faucet URLs above");
  console.log("   2. Enter your wallet address");
  console.log("   3. Complete any required verification");
  console.log("   4. Wait for funds to arrive (usually 30 seconds - 2 minutes)");
  console.log("   5. Check your balance: npx hardhat run scripts/check-balance.ts\n");

  console.log("🔗 Additional Resources:");
  console.log("   - Faucet aggregator: https://faucetlink.to/");
  console.log("   - Check testnet status: https://chainlist.org/\n");
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
