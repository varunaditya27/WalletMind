import { buildModule } from "@nomicfoundation/hardhat-ignition/modules";

/**
 * Hardhat Ignition module for deploying AgentRegistry contract
 * 
 * This module deploys the agent registry for:
 * - Agent discovery (FR-012)
 * - Reputation tracking
 * - Service listings for inter-agent communication
 */
export default buildModule("AgentRegistryModule", (m) => {
  // Deploy AgentRegistry contract
  const agentRegistry = m.contract("AgentRegistry", [], {
    id: "AgentRegistry",
  });

  return { agentRegistry };
});
