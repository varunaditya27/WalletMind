import { buildModule } from "@nomicfoundation/hardhat-ignition/modules";
import AgentWalletModule from "./AgentWallet.js";
import AgentRegistryModule from "./AgentRegistry.js";

/**
 * Complete deployment module for WalletMind system
 * 
 * Deploys both AgentWallet and AgentRegistry contracts
 * for a complete AI agent autonomous wallet system
 */
export default buildModule("WalletMindModule", (m) => {
  // Deploy AgentWallet
  const { agentWallet } = m.useModule(AgentWalletModule);

  // Deploy AgentRegistry
  const { agentRegistry } = m.useModule(AgentRegistryModule);

  return { agentWallet, agentRegistry };
});
