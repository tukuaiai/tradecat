# Resolution - Polymarket Documentation

URL: https://docs.polymarket.com/developers/resolution/UMA

---

Resolution - Polymarket Documentation

Skip to main content

Polymarket Documentation

home page

Search...

⌘

K

Search...

Navigation

Resolution

Resolution

User Guide

For Developers

Changelog

Polymarket

Discord Community

Twitter

Developer Quickstart

Developer Quickstart

Your First Order

Glossary

API Rate Limits

Endpoints

Central Limit Order Book

CLOB Introduction

Status

Clients

Authentication

CLOB Requests

Orderbook

Pricing

Spreads

Order Manipulation

Orders Overview

Place Single Order

Place Multiple Orders (Batching)

Get Order

Get Active Orders

Check Order Reward Scoring

Cancel Orders(s)

Onchain Order Info

Trades

Trades Overview

Get Trades

Websocket

WSS Overview

WSS Quickstart

WSS Authentication

User Channel

Market Channel

Real Time Data Stream

RTDS Overview

RTDS Crypto Prices

RTDS Comments

Gamma Structure

Overview

Gamma Structure

Fetching Markets

Gamma Endpoints

Health

Sports

Tags

Events

Markets

Series

Comments

Search

Data-API

Health

Core

Misc

Subgraph

Overview

Resolution

Resolution

Rewards

Liquidity Rewards

Conditional Token Frameworks

Overview

Splitting USDC

Merging Tokens

Reedeeming Tokens

Deployment and Additional Information

Proxy Wallets

Proxy wallet

Negative Risk

Overview

On this page

UMA Optimistic Oracle Integration

Overview

Clarifications

Resolution Process

Actions

Possible Flows

Deployed Addresses

v3.0

v2.0

v1.0

Additional Resources

​

UMA Optimistic Oracle Integration

​

Overview

Polymarket leverages UMA’s Optimistic Oracle (OO) to resolve arbitrary questions, permissionlessly. From

UMA’s docs

:

“UMA’s Optimistic Oracle allows contracts to quickly request and receive data information … The Optimistic Oracle acts as a generalized escalation game between contracts that initiate a price request and UMA’s dispute resolution system known as the Data Verification Mechanism (DVM). Prices proposed by the Optimistic Oracle will not be sent to the DVM unless it is disputed. If a dispute is raised, a request is sent to the DVM. All contracts built on UMA use the DVM as a backstop to resolve disputes. Disputes sent to the DVM will be resolved within a few days — after UMA tokenholders vote on what the correct outcome should have been.”

To allow CTF markets to be resolved via the OO, Polymarket developed a custom adapter contract called

UmaCtfAdapter

that provides a way for the two contract systems to interface.

​

Clarifications

Recent versions (v2+) of the

UmaCtfAdapter

also include a bulletin board feature that allows market creators to issue “clarifications”. Questions that allow updates will include the sentence in their ancillary data:

“Updates made by the question creator via the bulletin board on 0x6A5D0222186C0FceA7547534cC13c3CFd9b7b6A4F74 should be considered. In summary, clarifications that do not impact the question’s intent should be considered.”

Where the

transaction

reference outlining what outlining should be considered.

​

Resolution Process

​

Actions

Initiate

- Binary CTF markets are initialized via the

UmaCtfAdapter

’s

initialize()

function. This stores the question parameters on the contract, prepares the CTF and requests a price for a question from the OO. It returns a

questionID

that is also used to reference on the

UmaCtfAdapter

. The caller provides:

ancillaryData

- data used to resolve a question (i.e the question + clarifications)

rewardToken

- ERC20 token address used for payment of rewards and fees

reward

- Reward amount offered to a successful proposer. The caller must have set allowance so that the contract can pull this reward in.

proposalBond

- Bond required to be posted by OO proposers/disputers. If 0, the default OO bond is used.

liveness

- UMA liveness period in seconds. If 0, the default liveness period is used.

Propose Price

- Anyone can then propose a price to the question on the OO. To do this they must post the

proposalBond

. The liveness period begins after a price is proposed.

Dispute

- Anyone that disagrees with the proposed price has the opportunity to dispute the price by posting a counter bond via the OO, this proposed will now be escalated to the DVM for a voter-wide vote.

​

Possible Flows

When the first proposed price is disputed for a

questionID

on the adapter, a callback is made and posted as the reward for this new proposal. This means a second

questionID

, making a new

questionID

to the OO (the reward is returned before the callback is made and posted as the reward for this new proposal). This allows for a second round of resolution, and correspondingly a second dispute is required for it to go to the DVM. The thinking behind this is to doubles the cost of a potential griefing vector (two disputes are required just one) and also allows far-fetched (incorrect) first price proposals to not delay the resolution. As such there are two possible flows:

Initialize (CTFAdapter) -> Propose (OO) -> Resolve (CTFAdapter)

Initialize (CTFAdaptor) -> Propose (OO) -> Challenge (OO) -> Propose (OO) -> Resolve (CTFAdaptor)

Initialize (CTFAdaptor) -> Propose (OO) -> Challenge (OO) -> Propose (OO) -> Challenge (CtfAdapter) -> Resolve (CTFAdaptor)

​

Deployed Addresses

​

v3.0

Network

Address

Polygon Mainnet

0x2F5e3684cb1F318ec51b00Edba38d79Ac2c0aA9d

​

v2.0

Network

Address

Polygon Mainnet

0x6A9D0222186C0FceA7547534cC13c3CFd9b7b6A4F74

​

v1.0

Network

Address

Polygon Mainnet

0xC8B122858a4EF82C2d4eE2E6A276C719e692995130

​

Additional Resources

Audit

Source Code

UMA Documentation

UMA Oracle Portal

Overview

Liquidity Rewards

⌘

I