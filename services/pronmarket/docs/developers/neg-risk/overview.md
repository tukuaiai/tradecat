# Overview - Polymarket Documentation

URL: https://docs.polymarket.com/developers/neg-risk/overview

---

Overview - Polymarket Documentation

Skip to main content

Polymarket Documentation

home page

Search...

⌘

K

Search...

Navigation

Negative Risk

Overview

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

Augmented Negative Risk

Original Outcomes

Placeholder Outcomes

Explicit Other

Certain events which meet the criteria of being “winner-take-all” may be deployed as

“negative risk”

events/markets. The Gamma API includes a boolean field on events,

negRisk

, which indicates whether the event is negative risk.

Negative risk allows for increased capital efficiency by relating all markets within events via a convert action. More explicitly, a NO share in any market can be converted into 1 YES share in all other markets. Converts can be exercised via the

Negative Adapter

. You can read more about negative risk

here

.

​

Augmented Negative Risk

There is a known issue with the negative risk architecture which is that the outcome universe must be complete before conversions are made or otherwise conversion will “cost” something. In most cases, the outcome universe can be made complete by deploying all the named outcomes and then an “other” option. But in some cases this is undesirable as new outcomes can come out of nowhere and you’d rather them be directly named versus grouped together in an “other”.

To fix this, some markets use a system of

“augmented negative risk”

, where named outcomes, a collection of unnamed outcomes, and an

other

is deployed. When a new outcome needs to be added, an unnamed outcome can be clarified to be the new outcome via the bulletin board. This means the “other” in the case of augmented negative risk can effectively change definitions (outcomes can be taken out of it).

As such, trading should only happen on the named outcomes, and the other outcomes should be ignored until they are named or until resolution occurs. The Polymarket UI will not show unnamed outcomes.

If a market becomes resolvable and the correct outcome is not named (originally or via placeholder clarification), it should resolve to the

“other”

outcome. An event can be considered “augmented negative risk” when

enableNegRisk

is true

AND

negRiskAugmented

is true.

The naming conventions are as follows:

​

Original Outcomes

Outcome A

Outcome B

…

​

Placeholder Outcomes

Person A -> can be clarified to a named outcome

Person B -> can be clarified to a named outcome

…

​

Explicit Other

Other -> not meant to be traded as the definition of this changes as placeholder outcomes are clarified to named outcomes

Proxy wallet

⌘

I