# Clients - Polymarket Documentation

URL: https://docs.polymarket.com/developers/CLOB/clients

---

Clients - Polymarket Documentation

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

Order Utils

Polymarket has implemented reference clients that allow programmatic use of the API below:

clob-client

(Typescript)

py-clob-client

(Python)

python_initialization

typescript_initialization

Copy

Ask AI

pip install py

-

clob

-

client

from

py_clob_client.client

import

ClobClient

host:

str

=

""

key:

str

=

""

chain_id:

int

=

137

### Initialization of a client that trades directly from an EOA

client

=

ClobClient(host,

key

=

key,

chain_id

=

chain_id)

### Initialization of a client using a Polymarket Proxy associated with an Email/Magic account

client

=

ClobClient(host,

key

=

key,

chain_id

=

chain_id,

signature_type

=

1

,

funder

=

POLYMARKET_PROXY_ADDRESS

)

### Initialization of a client using a Polymarket Proxy associated with a Browser Wallet(Metamask, Coinbase Wallet, etc)

client

=

ClobClient(host,

key

=

key,

chain_id

=

chain_id,

signature_type

=

2

,

funder

=

POLYMARKET_PROXY_ADDRESS

)

​

Order Utils

Polymarket has implemented utility libraries to programmatically sign and generate orders:

clob-order-utils

(Typescript)

python-order-utils

(Python)

go-order-utils

(Golang)

Status

Authentication

⌘

I