import { describe, it } from "node:test";
import { expect } from "chai";
import hre from "hardhat";
import { getAddress, parseEther, keccak256, toHex } from "viem";

describe("AgentWallet", function () {
  // Fixture to deploy contract
  async function deployAgentWalletFixture() {
    const { viem } = await hre.network.connect();
    
    const [owner, agent, recipient] = await viem.getWalletClients();
    
    const agentWallet = await viem.deployContract("AgentWallet");
    
    const publicClient = await viem.getPublicClient();
    
    return {
      agentWallet,
      owner,
      agent,
      recipient,
      publicClient,
    };
  }

  describe("Deployment", function () {
    it("Should set the right owner", async function () {
      const { agentWallet, owner } = await deployAgentWalletFixture();
      expect(await agentWallet.read.owner()).to.equal(getAddress(owner.account.address));
    });

    it("Should initialize with default spending limit", async function () {
      const { agentWallet } = await deployAgentWalletFixture();
      const limit = await agentWallet.read.spendingLimits(["0x0000000000000000000000000000000000000000"]);
      expect(limit).to.equal(parseEther("0.1"));
    });

    it("Should not be paused initially", async function () {
      const { agentWallet } = await deployAgentWalletFixture();
      expect(await agentWallet.read.paused()).to.be.false;
    });
  });

  describe("Decision Logging (FR-007)", function () {
    it("Should log a decision successfully", async function () {
      const { agentWallet, agent } = await deployAgentWalletFixture();
      
      const decisionData = "AI decision: Transfer 0.01 ETH to recipient for API payment";
      const decisionHash = keccak256(toHex(decisionData));
      const ipfsCid = "QmExample123";
      
      await agentWallet.write.logDecision([decisionHash, ipfsCid], {
        account: agent.account,
      });
      
      const decision = await agentWallet.read.getDecision([decisionHash]);
      expect(decision.decisionHash).to.equal(decisionHash);
      expect(decision.ipfsProof).to.equal(ipfsCid);
      expect(decision.executor).to.equal(getAddress(agent.account.address));
      expect(decision.executed).to.be.false;
    });

    it("Should emit DecisionLogged event", async function () {
      const { agentWallet, agent, publicClient } = await deployAgentWalletFixture();
      
      const decisionHash = keccak256(toHex("test decision"));
      const ipfsCid = "QmTest";
      
      const hash = await agentWallet.write.logDecision([decisionHash, ipfsCid], {
        account: agent.account,
      });
      
      await publicClient.waitForTransactionReceipt({ hash });
      
      const logs = await agentWallet.getEvents.DecisionLogged();
      expect(logs).to.have.lengthOf(1);
      expect(logs[0].args.decisionHash).to.equal(decisionHash);
      expect(logs[0].args.ipfsProof).to.equal(ipfsCid);
    });

    it("Should reject invalid decision hash", async function () {
      const { agentWallet, agent } = await deployAgentWalletFixture();
      
      try {
        await agentWallet.write.logDecision(["0x0000000000000000000000000000000000000000000000000000000000000000", "QmTest"], {
          account: agent.account,
        });
        throw new Error("Should have reverted");
      } catch (error: any) {
        expect(error.message).to.include("AgentWallet: invalid decision hash");
      }
    });

    it("Should reject empty IPFS CID", async function () {
      const { agentWallet, agent } = await deployAgentWalletFixture();
      
      const decisionHash = keccak256(toHex("test"));
      
      try {
        await agentWallet.write.logDecision([decisionHash, ""], {
          account: agent.account,
        });
        throw new Error("Should have reverted");
      } catch (error: any) {
        expect(error.message).to.include("AgentWallet: IPFS CID required");
      }
    });

    it("Should prevent duplicate decision logging", async function () {
      const { agentWallet, agent } = await deployAgentWalletFixture();
      
      const decisionHash = keccak256(toHex("test"));
      
      await agentWallet.write.logDecision([decisionHash, "QmTest"], {
        account: agent.account,
      });
      
      try {
        await agentWallet.write.logDecision([decisionHash, "QmTest"], {
          account: agent.account,
        });
        throw new Error("Should have reverted");
      } catch (error: any) {
        expect(error.message).to.include("AgentWallet: decision already logged");
      }
    });
  });

  describe("Transaction Execution (FR-005, FR-007)", function () {
    it("Should execute a pre-logged decision", async function () {
      const { agentWallet, owner, agent, recipient, publicClient } = await deployAgentWalletFixture();
      
      // Fund the wallet
      await owner.sendTransaction({
        to: agentWallet.address,
        value: parseEther("0.05"),
      });
      
      // Log decision
      const decisionHash = keccak256(toHex("payment decision"));
      await agentWallet.write.logDecision([decisionHash, "QmPayment"], {
        account: agent.account,
      });
      
      // Execute decision
      const amount = parseEther("0.01");
      const hash = await agentWallet.write.verifyAndExecute(
        [decisionHash, recipient.account.address, amount],
        { account: owner.account }
      );
      
      await publicClient.waitForTransactionReceipt({ hash });
      
      // Verify decision was marked as executed
      const decision = await agentWallet.read.getDecision([decisionHash]);
      expect(decision.executed).to.be.true;
      expect(decision.amount).to.equal(amount);
      expect(decision.payee).to.equal(getAddress(recipient.account.address));
    });

    it("Should enforce spending limits (NFR-005)", async function () {
      const { agentWallet, owner, agent, recipient } = await deployAgentWalletFixture();
      
      // Fund wallet
      await owner.sendTransaction({
        to: agentWallet.address,
        value: parseEther("0.5"),
      });
      
      // Log decision
      const decisionHash = keccak256(toHex("large payment"));
      await agentWallet.write.logDecision([decisionHash, "QmLarge"], {
        account: agent.account,
      });
      
      // Try to exceed limit (default is 0.1 ETH)
      try {
        await agentWallet.write.verifyAndExecute(
          [decisionHash, recipient.account.address, parseEther("0.15")],
          { account: owner.account }
        );
        throw new Error("Should have reverted");
      } catch (error: any) {
        expect(error.message).to.include("AgentWallet: spending limit exceeded");
      }
    });

    it("Should reject execution without prior decision logging", async function () {
      const { agentWallet, owner, recipient } = await deployAgentWalletFixture();
      
      const decisionHash = keccak256(toHex("unlogged decision"));
      
      try {
        await agentWallet.write.verifyAndExecute(
          [decisionHash, recipient.account.address, parseEther("0.01")],
          { account: owner.account }
        );
        throw new Error("Should have reverted");
      } catch (error: any) {
        expect(error.message).to.include("AgentWallet: decision not logged");
      }
    });

    it("Should prevent double execution", async function () {
      const { agentWallet, owner, agent, recipient, publicClient } = await deployAgentWalletFixture();
      
      // Fund wallet
      await owner.sendTransaction({
        to: agentWallet.address,
        value: parseEther("0.1"),
      });
      
      // Log and execute
      const decisionHash = keccak256(toHex("double exec test"));
      await agentWallet.write.logDecision([decisionHash, "QmDouble"], {
        account: agent.account,
      });
      
      const hash = await agentWallet.write.verifyAndExecute(
        [decisionHash, recipient.account.address, parseEther("0.01")],
        { account: owner.account }
      );
      
      await publicClient.waitForTransactionReceipt({ hash });
      
      // Try to execute again
      try {
        await agentWallet.write.verifyAndExecute(
          [decisionHash, recipient.account.address, parseEther("0.01")],
          { account: owner.account }
        );
        throw new Error("Should have reverted");
      } catch (error: any) {
        expect(error.message).to.include("AgentWallet: decision already executed");
      }
    });

    it("Should emit DecisionExecuted and TransactionRecorded events (FR-008)", async function () {
      const { agentWallet, owner, agent, recipient, publicClient } = await deployAgentWalletFixture();
      
      // Fund wallet
      await owner.sendTransaction({
        to: agentWallet.address,
        value: parseEther("0.1"),
      });
      
      // Log and execute
      const decisionHash = keccak256(toHex("event test"));
      await agentWallet.write.logDecision([decisionHash, "QmEvent"], {
        account: agent.account,
      });
      
      const amount = parseEther("0.01");
      const hash = await agentWallet.write.verifyAndExecute(
        [decisionHash, recipient.account.address, amount],
        { account: owner.account }
      );
      
      await publicClient.waitForTransactionReceipt({ hash });
      
      // Check DecisionExecuted event
      const execLogs = await agentWallet.getEvents.DecisionExecuted();
      expect(execLogs).to.have.lengthOf(1);
      expect(execLogs[0].args.decisionHash).to.equal(decisionHash);
      expect(execLogs[0].args.payee).to.equal(getAddress(recipient.account.address));
      expect(execLogs[0].args.amount).to.equal(amount);
      
      // Check TransactionRecorded event
      const txLogs = await agentWallet.getEvents.TransactionRecorded();
      expect(txLogs).to.have.lengthOf(1);
    });
  });

  describe("Spending Limits (NFR-005)", function () {
    it("Should allow owner to update spending limits", async function () {
      const { agentWallet, owner } = await deployAgentWalletFixture();
      
      const newLimit = parseEther("0.5");
      await agentWallet.write.setSpendingLimit(
        ["0x0000000000000000000000000000000000000000", newLimit],
        { account: owner.account }
      );
      
      const limit = await agentWallet.read.spendingLimits(["0x0000000000000000000000000000000000000000"]);
      expect(limit).to.equal(newLimit);
    });

    it("Should track total spent amount", async function () {
      const { agentWallet, owner, agent, recipient, publicClient } = await deployAgentWalletFixture();
      
      // Fund wallet
      await owner.sendTransaction({
        to: agentWallet.address,
        value: parseEther("0.1"),
      });
      
      // Execute first transaction
      const hash1 = keccak256(toHex("tx1"));
      await agentWallet.write.logDecision([hash1, "Qm1"], { account: agent.account });
      const amount1 = parseEther("0.02");
      await agentWallet.write.verifyAndExecute([hash1, recipient.account.address, amount1], { account: owner.account });
      
      // Execute second transaction
      const hash2 = keccak256(toHex("tx2"));
      await agentWallet.write.logDecision([hash2, "Qm2"], { account: agent.account });
      const amount2 = parseEther("0.03");
      const hash = await agentWallet.write.verifyAndExecute([hash2, recipient.account.address, amount2], { account: owner.account });
      
      await publicClient.waitForTransactionReceipt({ hash });
      
      const totalSpent = await agentWallet.read.totalSpent(["0x0000000000000000000000000000000000000000"]);
      expect(totalSpent).to.equal(amount1 + amount2);
    });

    it("Should allow owner to reset spent amount", async function () {
      const { agentWallet, owner, agent, recipient, publicClient } = await deployAgentWalletFixture();
      
      // Fund and execute transaction
      await owner.sendTransaction({
        to: agentWallet.address,
        value: parseEther("0.1"),
      });
      
      const hash1 = keccak256(toHex("reset test"));
      await agentWallet.write.logDecision([hash1, "QmReset"], { account: agent.account });
      const h = await agentWallet.write.verifyAndExecute([hash1, recipient.account.address, parseEther("0.02")], { account: owner.account });
      await publicClient.waitForTransactionReceipt({ hash: h });
      
      // Reset
      await agentWallet.write.resetSpentAmount(["0x0000000000000000000000000000000000000000"], {
        account: owner.account,
      });
      
      const totalSpent = await agentWallet.read.totalSpent(["0x0000000000000000000000000000000000000000"]);
      expect(totalSpent).to.equal(0n);
    });
  });

  describe("Emergency Pause (NFR-005)", function () {
    it("Should allow owner to pause contract", async function () {
      const { agentWallet, owner } = await deployAgentWalletFixture();
      
      await agentWallet.write.setPaused([true], { account: owner.account });
      expect(await agentWallet.read.paused()).to.be.true;
    });

    it("Should prevent operations when paused", async function () {
      const { agentWallet, owner, agent } = await deployAgentWalletFixture();
      
      await agentWallet.write.setPaused([true], { account: owner.account });
      
      const decisionHash = keccak256(toHex("paused test"));
      
      try {
        await agentWallet.write.logDecision([decisionHash, "QmPaused"], {
          account: agent.account,
        });
        throw new Error("Should have reverted");
      } catch (error: any) {
        expect(error.message).to.include("AgentWallet: contract is paused");
      }
    });

    it("Should allow unpausing", async function () {
      const { agentWallet, owner, agent } = await deployAgentWalletFixture();
      
      // Pause
      await agentWallet.write.setPaused([true], { account: owner.account });
      
      // Unpause
      await agentWallet.write.setPaused([false], { account: owner.account });
      
      // Should work now
      const decisionHash = keccak256(toHex("unpause test"));
      await agentWallet.write.logDecision([decisionHash, "QmUnpause"], {
        account: agent.account,
      });
      
      const decision = await agentWallet.read.getDecision([decisionHash]);
      expect(decision.decisionHash).to.equal(decisionHash);
    });
  });

  describe("Transaction History (FR-008)", function () {
    it("Should track transaction count", async function () {
      const { agentWallet, owner, agent, recipient, publicClient } = await deployAgentWalletFixture();
      
      // Fund wallet
      await owner.sendTransaction({
        to: agentWallet.address,
        value: parseEther("0.1"),
      });
      
      // Execute transactions
      for (let i = 0; i < 3; i++) {
        const hash = keccak256(toHex(`tx${i}`));
        await agentWallet.write.logDecision([hash, `Qm${i}`], { account: agent.account });
        const h = await agentWallet.write.verifyAndExecute(
          [hash, recipient.account.address, parseEther("0.01")],
          { account: owner.account }
        );
        await publicClient.waitForTransactionReceipt({ hash: h });
      }
      
      const count = await agentWallet.read.getTransactionCount();
      expect(count).to.equal(3n);
    });

    it("Should store complete transaction records", async function () {
      const { agentWallet, owner, agent, recipient, publicClient } = await deployAgentWalletFixture();
      
      // Fund wallet
      await owner.sendTransaction({
        to: agentWallet.address,
        value: parseEther("0.1"),
      });
      
      // Execute transaction
      const decisionHash = keccak256(toHex("record test"));
      await agentWallet.write.logDecision([decisionHash, "QmRecord"], { account: agent.account });
      
      const amount = parseEther("0.01");
      const hash = await agentWallet.write.verifyAndExecute(
        [decisionHash, recipient.account.address, amount],
        { account: owner.account }
      );
      
      await publicClient.waitForTransactionReceipt({ hash });
      
      const record = await agentWallet.read.getTransaction([0n]);
      expect(record.decisionHash).to.equal(decisionHash);
      expect(record.to).to.equal(getAddress(recipient.account.address));
      expect(record.value).to.equal(amount);
      expect(record.category).to.equal("autonomous_payment");
      expect(record.success).to.be.true;
    });
  });

  describe("Access Control", function () {
    it("Should only allow owner to execute decisions", async function () {
      const { agentWallet, agent, recipient } = await deployAgentWalletFixture();
      
      const decisionHash = keccak256(toHex("access test"));
      await agentWallet.write.logDecision([decisionHash, "QmAccess"], {
        account: agent.account,
      });
      
      try {
        await agentWallet.write.verifyAndExecute(
          [decisionHash, recipient.account.address, parseEther("0.01")],
          { account: agent.account }
        );
        throw new Error("Should have reverted");
      } catch (error: any) {
        expect(error.message).to.include("AgentWallet: caller is not the owner");
      }
    });

    it("Should allow ownership transfer", async function () {
      const { agentWallet, owner, agent } = await deployAgentWalletFixture();
      
      await agentWallet.write.transferOwnership([agent.account.address], {
        account: owner.account,
      });
      
      expect(await agentWallet.read.owner()).to.equal(getAddress(agent.account.address));
    });
  });

  describe("Wallet Functions", function () {
    it("Should receive ETH", async function () {
      const { agentWallet, owner } = await deployAgentWalletFixture();
      
      const amount = parseEther("1.0");
      await owner.sendTransaction({
        to: agentWallet.address,
        value: amount,
      });
      
      const balance = await agentWallet.read.getBalance();
      expect(balance).to.equal(amount);
    });

    it("Should allow owner to withdraw", async function () {
      const { agentWallet, owner, publicClient } = await deployAgentWalletFixture();
      
      // Fund wallet
      const amount = parseEther("1.0");
      await owner.sendTransaction({
        to: agentWallet.address,
        value: amount,
      });
      
      // Withdraw
      const withdrawAmount = parseEther("0.5");
      const hash = await agentWallet.write.withdraw([withdrawAmount], {
        account: owner.account,
      });
      
      await publicClient.waitForTransactionReceipt({ hash });
      
      const balance = await agentWallet.read.getBalance();
      expect(balance).to.equal(amount - withdrawAmount);
    });
  });
});
