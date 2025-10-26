import { buildModule } from "@nomicfoundation/hardhat-ignition/modules";

/**
 * Hardhat Ignition module for deploying AgentWallet contract
 * 
 * This module deploys the main AI agent wallet with:
 * - Decision provenance logging (FR-007)
 * - On-chain audit trail (FR-008)
 * - Spending limits enforcement (NFR-005)
 */
export default buildModule("AgentWalletModule", (m) => {
  // Deploy AgentWallet contract
  const agentWallet = m.contract("AgentWallet", [], {
    id: "AgentWallet",
  });

  return { agentWallet };
});
