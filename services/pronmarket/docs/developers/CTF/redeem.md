# Reedeeming Tokens - Polymarket Documentation

URL: https://docs.polymarket.com/developers/CTF/redeem

---

Reedeeming Tokens - Polymarket Documentation

Skip to main content

Polymarket Documentation

home page

Search...

⌘

K

Search...

Navigation

Conditional Token Frameworks

Reedeeming Tokens

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

Once a condition has had it’s payouts reported (ie by the UMACTFAdapter calling

reportPayouts

on the CTF contract), users with shares in the winning outcome can redeem them for the underlying collateral. Specifically, users can call the

redeemPositions

function on the CTF contract which will burn all valuable conditional tokens in return for collateral according to the reported payout vector. This function has the following parameters:

collateralToken

: IERC20 - The address of the positions’ backing collateral token.

parentCollectionId

: bytes32 - The ID of the outcome collections common to the position being redeemed. Null in Polymarket case.

indexSets

: uint[] - The ID of the condition to redeem.

indexSets

: uint[] - An array of disjoint index sets representing a nontrivial partition of the outcome slots of the given condition. E.G. A|B and C but not A|B and B|C (is not disjoint). Each element’s a number which, together with the condition, represents the outcome collection. E.G. 0b110 is A|B, 0b010 is B, etc. In the Polymarket case 1|2.

Merging Tokens

Deployment and Additional Information

⌘

I