# WSS Overview - Polymarket Documentation

URL: https://docs.polymarket.com/developers/CLOB/websocket/wss-overview

---

WSS Overview - Polymarket Documentation

Skip to main content

Polymarket Documentation

home page

Search...

⌘

K

Search...

Navigation

Websocket

WSS Overview

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

Subscription

​

Overview

The Polymarket CLOB API provides websocket (wss) channels through which clients can get pushed updates. These endpoints allow clients to maintain almost real-time views of their orders, their trades and markets in general. There are two available channels

user

and

market

.

​

Subscription

To subscribe send a message including the following authentication and intent information upon opening the connection.

Field

Type

Description

auth

Auth

see next page for auth information

markets

string[]

array of markets (condition IDs) to receive events for (for

user

channel)

assets_ids

string[]

array of asset ids (token IDs) to receive events for (for

market

channel)

type

string

id of channel to subscribe to (USER or MARKET)

Where the

auth

field is of type

Auth

which has the form described in the WSS Authentication section below.

Get Trades

WSS Quickstart

⌘

I