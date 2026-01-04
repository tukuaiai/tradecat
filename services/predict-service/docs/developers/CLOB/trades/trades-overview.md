# Trades Overview - Polymarket Documentation

URL: https://docs.polymarket.com/developers/CLOB/trades/trades-overview

---

Trades Overview - Polymarket Documentation

Skip to main content

Polymarket Documentation

home page

Search...

⌘

K

Search...

Navigation

Trades

Trades Overview

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

Overview

Statuses

​

Overview

All historical trades can be fetched via the Polymarket CLOB REST API. A trade is initiated by a “taker” who creates a marketable limit order. This limit order can be matched against one or more resting limit orders on the associated book. A trade can be in various states as described below. Note: in some cases (due to gas limitations) the execution of a “trade” must be broken into multiple transactions which case separate trade entities will be returned. To associate trade entities, there is a bucket_index field and a match_time field. Trades that have been broken into multiple trade objects can be reconciled by combining trade objects with the same market_order_id, match_time and incrementing bucket_index’s into a top level “trade” client side.

​

Statuses

Status

Terminal?

Description

MATCHED

no

trade has been matched and sent to the executor service by the operator, the executor service submits the trade as a transaction to the Exchange contract

MINED

no

trade is observed to be mined into the chain, no finality threshold established

CONFIRMED

yes

trade has achieved strong probabilistic finality and was successful

RETRYING

no

trade transaction has failed (revert or reorg) and is being retried/resubmitted by the operator

FAILED

yes

trade has failed and is not being retried

Onchain Order Info

Get Trades

⌘

I