import { parseEther } from "viem";

/**
 * Script to request testnet funds from Sepolia faucets
 */
async function main() {
  console.log("\n💰 Sepolia Testnet Faucet Information\n");
  console.log("=" .repeat(60));

  const account = process.env.SEPOLIA_PRIVATE_KEY 
    ? "0x" + process.env.SEPOLIA_PRIVATE_KEY.slice(0, 10) + "..." 
    : "Not configured";

  console.log(`\n📝 Your account: ${account}`);
  console.log("\n🚰 Sepolia ETH Faucets:\n");

  console.log("1️⃣  Alchemy Faucet (Recommended)");
  console.log("   URL: https://sepoliafaucet.com/");
  console.log("   Amount: 0.5 ETH per request");
  console.log("   Requirements: Alchemy account (free)\n");

  console.log("2️⃣  QuickNode Faucet");
  console.log("   URL: https://faucet.quicknode.com/ethereum/sepolia");
  console.log("   Amount: 0.05-0.1 ETH per request");
  console.log("   Requirements: Twitter account\n");

  console.log("3️⃣  Google Cloud Faucet");
  console.log("   URL: https://cloud.google.com/application/web3/faucet/ethereum/sepolia");
  console.log("   Amount: 0.05 ETH per request");
  console.log("   Requirements: Google account\n");

  console.log("4️⃣  Infura Faucet");
  console.log("   URL: https://www.infura.io/faucet/sepolia");
  console.log("   Amount: 0.5 ETH per request");
  console.log("   Requirements: Infura account\n");

  console.log("=" .repeat(60));

  console.log("\n💡 Tips:");
  console.log("   • Request from multiple faucets for more funds");
  console.log("   • Keep at least 0.05 ETH for gas fees");
  console.log("   • Most faucets have rate limits (1 request per 24h)");
  console.log("   • Testnet ETH has NO real-world value");

  console.log("\n📋 Steps to Get Testnet ETH:");
  console.log("   1. Visit one of the faucet URLs above");
  console.log("   2. Connect your Metamask wallet OR paste your address");
  console.log("   3. Complete any required verification (Twitter, etc.)");
  console.log("   4. Wait for funds (usually 30 seconds - 2 minutes)");
  console.log("   5. Check balance: npm run check:balance\n");

  console.log("🔗 Useful Links:");
  console.log("   • Sepolia Explorer: https://sepolia.etherscan.io/");
  console.log("   • Alchemy Dashboard: https://dashboard.alchemy.com/");
  console.log("   • Metamask: https://metamask.io/\n");
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
