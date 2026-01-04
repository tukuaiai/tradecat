# Overview - Polymarket Documentation

URL: https://docs.polymarket.com/developers/subgraph/overview

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

Subgraph Overview

Source

Hosted Version

​

Subgraph Overview

Polymarket has written and open sourced a subgraph that provides, via a GraphQL query interface, useful aggregate calculations and event indexing for things like volume, user position, market and liquidity data. The subgraph updates in real time to be able to be mixed, and match core data from the primary Polymarket interface, providing positional data, activity history and more. The subgraph can be hosted by anyone but is also hosted and made publicly available by a 3rd party provider, Goldsky.

​

Source

The Polymarket subgraph is entirely open source and can be found on the Polymarket Github.

Subgraph Github Repository

Note: The available models/schemas can be found in the

schema.graphql

file.

​

Hosted Version

The subgraphs are hosted on goldsky, each with an accompanying GraphQL playground:

Orders subgraph:

https://api.goldsky.com/api/public/project_cl6mb8i9h0003e201j6li0diw/subgraphs/orderbook-subgraph/0.0.1/gn

Positions subgraph:

https://api.goldsky.com/api/public/project_cl6mb8i9h0003e201j6li0diw/subgraphs/positions-subgraph/0.0.7/gn

Activity subgraph:

https://api.goldsky.com/api/public/project_cl6mb8i9h0003e201j6li0diw/subgraphs/activity-subgraph/0.0.4/gn

Open Interest subgraph:

https://api.goldsky.com/api/public/project_cl6mb8i9h0003e201j6li0diw/subgraphs/oi-subgraph/0.0.6/gn

PNL subgraph:

https://api.goldsky.com/api/public/project_cl6mb8i9h0003e201j6li0diw/subgraphs/pnl-subgraph/0.0.14/gn

Get live volume for an event

Resolution

⌘

I