import { loadFixture } from "@nomicfoundation/hardhat-toolbox-viem/network-helpers";
import { expect } from "chai";
import hre from "hardhat";
import { getAddress } from "viem";

describe("AgentRegistry", function () {
  // Fixture to deploy contract
  async function deployAgentRegistryFixture() {
    const [admin, agent1, agent2, agent3] = await hre.viem.getWalletClients();
    
    const agentRegistry = await hre.viem.deployContract("AgentRegistry");
    
    const publicClient = await hre.viem.getPublicClient();
    
    return {
      agentRegistry,
      admin,
      agent1,
      agent2,
      agent3,
      publicClient,
    };
  }

  describe("Deployment", function () {
    it("Should set the right admin", async function () {
      const { agentRegistry, admin } = await loadFixture(deployAgentRegistryFixture);
      expect(await agentRegistry.read.admin()).to.equal(getAddress(admin.account.address));
    });

    it("Should initialize with zero agents", async function () {
      const { agentRegistry } = await loadFixture(deployAgentRegistryFixture);
      expect(await agentRegistry.read.agentCount()).to.equal(0n);
    });
  });

  describe("Agent Registration (FR-012)", function () {
    it("Should register a new agent", async function () {
      const { agentRegistry, agent1 } = await loadFixture(deployAgentRegistryFixture);
      
      const metadata = JSON.stringify({
        name: "AI Agent 1",
        capabilities: ["payment", "data_analysis"],
        version: "1.0.0",
      });
      
      await agentRegistry.write.registerAgent([metadata], {
        account: agent1.account,
      });
      
      const agent = await agentRegistry.read.getAgent([agent1.account.address]);
      expect(agent.wallet).to.equal(getAddress(agent1.account.address));
      expect(agent.metadata).to.equal(metadata);
      expect(agent.reputation).to.equal(500n); // Neutral reputation
      expect(agent.active).to.be.true;
    });

    it("Should emit AgentRegistered event", async function () {
      const { agentRegistry, agent1, publicClient } = await loadFixture(deployAgentRegistryFixture);
      
      const metadata = "{ \"name\": \"Test Agent\" }";
      
      const hash = await agentRegistry.write.registerAgent([metadata], {
        account: agent1.account,
      });
      
      await publicClient.waitForTransactionReceipt({ hash });
      
      const logs = await agentRegistry.getEvents.AgentRegistered();
      expect(logs).to.have.lengthOf(1);
      expect(logs[0].args.agentAddress).to.equal(getAddress(agent1.account.address));
    });

    it("Should increment agent count", async function () {
      const { agentRegistry, agent1, agent2 } = await loadFixture(deployAgentRegistryFixture);
      
      await agentRegistry.write.registerAgent(["metadata1"], {
        account: agent1.account,
      });
      
      await agentRegistry.write.registerAgent(["metadata2"], {
        account: agent2.account,
      });
      
      expect(await agentRegistry.read.agentCount()).to.equal(2n);
    });

    it("Should prevent duplicate registration", async function () {
      const { agentRegistry, agent1 } = await loadFixture(deployAgentRegistryFixture);
      
      await agentRegistry.write.registerAgent(["metadata1"], {
        account: agent1.account,
      });
      
      await expect(
        agentRegistry.write.registerAgent(["metadata2"], {
          account: agent1.account,
        })
      ).to.be.rejectedWith("AgentRegistry: already registered");
    });

    it("Should require metadata", async function () {
      const { agentRegistry, agent1 } = await loadFixture(deployAgentRegistryFixture);
      
      await expect(
        agentRegistry.write.registerAgent([""], {
          account: agent1.account,
        })
      ).to.be.rejectedWith("AgentRegistry: metadata required");
    });
  });

  describe("Agent Discovery", function () {
    it("Should return all registered agents", async function () {
      const { agentRegistry, agent1, agent2, agent3 } = await loadFixture(deployAgentRegistryFixture);
      
      await agentRegistry.write.registerAgent(["meta1"], { account: agent1.account });
      await agentRegistry.write.registerAgent(["meta2"], { account: agent2.account });
      await agentRegistry.write.registerAgent(["meta3"], { account: agent3.account });
      
      const allAgents = await agentRegistry.read.getAllAgents();
      expect(allAgents).to.have.lengthOf(3);
      expect(allAgents).to.include(getAddress(agent1.account.address));
      expect(allAgents).to.include(getAddress(agent2.account.address));
      expect(allAgents).to.include(getAddress(agent3.account.address));
    });

    it("Should return only active agents", async function () {
      const { agentRegistry, agent1, agent2, agent3 } = await loadFixture(deployAgentRegistryFixture);
      
      // Register agents
      await agentRegistry.write.registerAgent(["meta1"], { account: agent1.account });
      await agentRegistry.write.registerAgent(["meta2"], { account: agent2.account });
      await agentRegistry.write.registerAgent(["meta3"], { account: agent3.account });
      
      // Deactivate agent2
      await agentRegistry.write.setActiveStatus([false], { account: agent2.account });
      
      const activeAgents = await agentRegistry.read.getActiveAgents();
      expect(activeAgents).to.have.lengthOf(2);
      expect(activeAgents).to.include(getAddress(agent1.account.address));
      expect(activeAgents).to.include(getAddress(agent3.account.address));
      expect(activeAgents).to.not.include(getAddress(agent2.account.address));
    });
  });

  describe("Reputation Management", function () {
    it("Should update reputation on successful transaction", async function () {
      const { agentRegistry, agent1 } = await loadFixture(deployAgentRegistryFixture);
      
      await agentRegistry.write.registerAgent(["metadata"], {
        account: agent1.account,
      });
      
      // Success increases reputation
      await agentRegistry.write.updateReputation([agent1.account.address, true]);
      
      const agent = await agentRegistry.read.getAgent([agent1.account.address]);
      expect(agent.reputation).to.equal(510n); // 500 + 10
      expect(agent.transactionCount).to.equal(1n);
      expect(agent.successfulTxCount).to.equal(1n);
    });

    it("Should decrease reputation on failed transaction", async function () {
      const { agentRegistry, agent1 } = await loadFixture(deployAgentRegistryFixture);
      
      await agentRegistry.write.registerAgent(["metadata"], {
        account: agent1.account,
      });
      
      // Failure decreases reputation
      await agentRegistry.write.updateReputation([agent1.account.address, false]);
      
      const agent = await agentRegistry.read.getAgent([agent1.account.address]);
      expect(agent.reputation).to.equal(480n); // 500 - 20
      expect(agent.transactionCount).to.equal(1n);
      expect(agent.successfulTxCount).to.equal(0n);
    });

    it("Should cap reputation at 1000", async function () {
      const { agentRegistry, agent1 } = await loadFixture(deployAgentRegistryFixture);
      
      await agentRegistry.write.registerAgent(["metadata"], {
        account: agent1.account,
      });
      
      // Execute many successful transactions
      for (let i = 0; i < 60; i++) {
        await agentRegistry.write.updateReputation([agent1.account.address, true]);
      }
      
      const agent = await agentRegistry.read.getAgent([agent1.account.address]);
      expect(agent.reputation).to.equal(1000n); // Capped at max
    });

    it("Should not go below 0 reputation", async function () {
      const { agentRegistry, agent1 } = await loadFixture(deployAgentRegistryFixture);
      
      await agentRegistry.write.registerAgent(["metadata"], {
        account: agent1.account,
      });
      
      // Execute many failed transactions
      for (let i = 0; i < 30; i++) {
        await agentRegistry.write.updateReputation([agent1.account.address, false]);
      }
      
      const agent = await agentRegistry.read.getAgent([agent1.account.address]);
      expect(agent.reputation).to.equal(0n); // Capped at min
    });

    it("Should calculate success rate correctly", async function () {
      const { agentRegistry, agent1 } = await loadFixture(deployAgentRegistryFixture);
      
      await agentRegistry.write.registerAgent(["metadata"], {
        account: agent1.account,
      });
      
      // 3 successes, 2 failures = 60% success rate
      await agentRegistry.write.updateReputation([agent1.account.address, true]);
      await agentRegistry.write.updateReputation([agent1.account.address, true]);
      await agentRegistry.write.updateReputation([agent1.account.address, false]);
      await agentRegistry.write.updateReputation([agent1.account.address, true]);
      await agentRegistry.write.updateReputation([agent1.account.address, false]);
      
      const successRate = await agentRegistry.read.getSuccessRate([agent1.account.address]);
      expect(successRate).to.equal(60n); // 3/5 * 100
    });
  });

  describe("Service Management (FR-012)", function () {
    it("Should register a service offering", async function () {
      const { agentRegistry, agent1 } = await loadFixture(deployAgentRegistryFixture);
      
      await agentRegistry.write.registerAgent(["metadata"], {
        account: agent1.account,
      });
      
      const serviceId = "data_analysis";
      const price = 1000000000000000n; // 0.001 ETH
      const description = "AI-powered data analysis service";
      
      await agentRegistry.write.registerService([serviceId, price, description], {
        account: agent1.account,
      });
      
      const service = await agentRegistry.read.getService([agent1.account.address, serviceId]);
      expect(service.serviceId).to.equal(serviceId);
      expect(service.provider).to.equal(getAddress(agent1.account.address));
      expect(service.price).to.equal(price);
      expect(service.available).to.be.true;
    });

    it("Should prevent service registration without agent registration", async function () {
      const { agentRegistry, agent1 } = await loadFixture(deployAgentRegistryFixture);
      
      await expect(
        agentRegistry.write.registerService(["service1", 1000n, "desc"], {
          account: agent1.account,
        })
      ).to.be.rejectedWith("AgentRegistry: agent not registered");
    });

    it("Should update service availability", async function () {
      const { agentRegistry, agent1 } = await loadFixture(deployAgentRegistryFixture);
      
      await agentRegistry.write.registerAgent(["metadata"], {
        account: agent1.account,
      });
      
      const serviceId = "service1";
      await agentRegistry.write.registerService([serviceId, 1000n, "desc"], {
        account: agent1.account,
      });
      
      // Make unavailable
      await agentRegistry.write.updateServiceAvailability([serviceId, false], {
        account: agent1.account,
      });
      
      const service = await agentRegistry.read.getService([agent1.account.address, serviceId]);
      expect(service.available).to.be.false;
    });

    it("Should track multiple services per agent", async function () {
      const { agentRegistry, agent1 } = await loadFixture(deployAgentRegistryFixture);
      
      await agentRegistry.write.registerAgent(["metadata"], {
        account: agent1.account,
      });
      
      await agentRegistry.write.registerService(["service1", 1000n, "desc1"], {
        account: agent1.account,
      });
      await agentRegistry.write.registerService(["service2", 2000n, "desc2"], {
        account: agent1.account,
      });
      await agentRegistry.write.registerService(["service3", 3000n, "desc3"], {
        account: agent1.account,
      });
      
      const services = await agentRegistry.read.getAgentServices([agent1.account.address]);
      expect(services).to.have.lengthOf(3);
    });
  });

  describe("Agent Status Management", function () {
    it("Should allow agent to set active status", async function () {
      const { agentRegistry, agent1 } = await loadFixture(deployAgentRegistryFixture);
      
      await agentRegistry.write.registerAgent(["metadata"], {
        account: agent1.account,
      });
      
      await agentRegistry.write.setActiveStatus([false], {
        account: agent1.account,
      });
      
      const agent = await agentRegistry.read.getAgent([agent1.account.address]);
      expect(agent.active).to.be.false;
    });

    it("Should emit AgentStatusChanged event", async function () {
      const { agentRegistry, agent1, publicClient } = await loadFixture(deployAgentRegistryFixture);
      
      await agentRegistry.write.registerAgent(["metadata"], {
        account: agent1.account,
      });
      
      const hash = await agentRegistry.write.setActiveStatus([false], {
        account: agent1.account,
      });
      
      await publicClient.waitForTransactionReceipt({ hash });
      
      const logs = await agentRegistry.getEvents.AgentStatusChanged();
      expect(logs).to.have.lengthOf(1);
      expect(logs[0].args.active).to.be.false;
    });
  });

  describe("Metadata Updates", function () {
    it("Should allow registered agent to update metadata", async function () {
      const { agentRegistry, agent1 } = await loadFixture(deployAgentRegistryFixture);
      
      await agentRegistry.write.registerAgent(["old metadata"], {
        account: agent1.account,
      });
      
      const newMetadata = JSON.stringify({ updated: true });
      await agentRegistry.write.updateMetadata([newMetadata], {
        account: agent1.account,
      });
      
      const agent = await agentRegistry.read.getAgent([agent1.account.address]);
      expect(agent.metadata).to.equal(newMetadata);
    });

    it("Should require agent to be registered for metadata update", async function () {
      const { agentRegistry, agent1 } = await loadFixture(deployAgentRegistryFixture);
      
      await expect(
        agentRegistry.write.updateMetadata(["new metadata"], {
          account: agent1.account,
        })
      ).to.be.rejectedWith("AgentRegistry: agent not registered");
    });
  });

  describe("Access Control", function () {
    it("Should allow admin transfer", async function () {
      const { agentRegistry, admin, agent1 } = await loadFixture(deployAgentRegistryFixture);
      
      await agentRegistry.write.transferAdmin([agent1.account.address], {
        account: admin.account,
      });
      
      expect(await agentRegistry.read.admin()).to.equal(getAddress(agent1.account.address));
    });

    it("Should reject admin transfer from non-admin", async function () {
      const { agentRegistry, agent1, agent2 } = await loadFixture(deployAgentRegistryFixture);
      
      await expect(
        agentRegistry.write.transferAdmin([agent2.account.address], {
          account: agent1.account,
        })
      ).to.be.rejectedWith("AgentRegistry: caller is not admin");
    });
  });
});
