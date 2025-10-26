import type { HardhatUserConfig } from "hardhat/config";

import hardhatToolboxViemPlugin from "@nomicfoundation/hardhat-toolbox-viem";
import { configVariable } from "hardhat/config";

const config: HardhatUserConfig = {
  plugins: [hardhatToolboxViemPlugin],
  solidity: {
    profiles: {
      default: {
        version: "0.8.28",
        settings: {
          optimizer: {
            enabled: true,
            runs: 200,
          },
          evmVersion: "paris", // Compatible with most networks
        },
      },
      production: {
        version: "0.8.28",
        settings: {
          optimizer: {
            enabled: true,
            runs: 1000, // Higher runs for production
          },
          evmVersion: "paris",
        },
      },
    },
  },
  networks: {
    // Local development networks
    hardhatMainnet: {
      type: "edr-simulated",
      chainType: "l1",
    },
    hardhatOp: {
      type: "edr-simulated",
      chainType: "op",
    },
    
    // Ethereum Sepolia Testnet (FR-006)
    sepolia: {
      type: "http",
      chainType: "l1",
      url: configVariable("SEPOLIA_RPC_URL", {
        example: "https://sepolia.infura.io/v3/YOUR_INFURA_KEY",
      }),
      accounts: [configVariable("SEPOLIA_PRIVATE_KEY")],
      gasPrice: "auto",
    },
    
    // Polygon Amoy Testnet (FR-006)
    polygonAmoy: {
      type: "http",
      chainType: "l1",
      url: configVariable("POLYGON_AMOY_RPC_URL", {
        example: "https://rpc-amoy.polygon.technology",
        defaultValue: "https://rpc-amoy.polygon.technology",
      }),
      accounts: [configVariable("POLYGON_AMOY_PRIVATE_KEY")],
      gasPrice: "auto",
    },
    
    // Base Sepolia Testnet (FR-006)
    baseSepolia: {
      type: "http",
      chainType: "op",
      url: configVariable("BASE_SEPOLIA_RPC_URL", {
        example: "https://sepolia.base.org",
        defaultValue: "https://sepolia.base.org",
      }),
      accounts: [configVariable("BASE_SEPOLIA_PRIVATE_KEY")],
      gasPrice: "auto",
    },
  },
  paths: {
    sources: "./contracts",
    tests: "./test",
    cache: "./cache",
    artifacts: "./artifacts",
    ignition: "./ignition",
  },
  mocha: {
    timeout: 60000, // 60 seconds for testnet transactions
  },
};

export default config;
