# Your First Order - Polymarket Documentation

URL: https://docs.polymarket.com/quickstart/orders/first-order

---

Your First Order - Polymarket Documentation

Skip to main content

Polymarket Documentation

home page

Search...

⌘

K

Search...

Navigation

Developer Quickstart

Your First Order

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

In addition to detailed comments in the code snippet, here are some more tips to help you get started.

Placing your first order using one of our two Clients is relatively straightforward.

For Python:

pip install py-clob-client

.

For Typescript:

npm install polymarket/clob-client

&

npm install ethers

.

After installing one of those you will be able to run the below code. Take the time to fill in the constants at the top and ensure you’re using the proper signature type based on your login method.

Many additional examples for the Typescript and Python clients are available

here(TS)

and

here(Python)

.

Python First Trade

Typescript First Trade

Copy

Ask AI

from

py_clob_client.client

import

ClobClient

from

py_clob_client.clob_types

import

OrderArgs, OrderType

from

py_clob_client.order_builder.constants

import

BUY

host:

str

=

"https://clob.polymarket.com"

key:

str

=

""

#This is your Private Key. Export from https://reveal.magic.link/polymarket or from your Web3 Extension

chain_id:

int

=

137

#No need to adjust this

POLYMARKET_PROXY_ADDRESS

:

str

=

''

#This is the address listed below your profile picture when using the Polymarket site.

#Select from the following 3 initialization options to match your login method, and remove any unused lines so only one client is initialized.

### Initialization of a client using a Polymarket Proxy associated with an Email/Magic account. If you login with your email use this example.

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

### Initialization of a client that trades directly from an EOA. (If you don't know what this means, you're not using it)

client

=

ClobClient(host,

key

=

key,

chain_id

=

chain_id)

## Create and sign a limit order buying 5 tokens for 0.010c each

#Refer to the API documentation to locate a tokenID: https://docs.polymarket.com/developers/gamma-markets-api/fetch-markets-guide

client.set_api_creds(client.create_or_derive_api_creds())

order_args

=

OrderArgs(

price

=

0.01

,

size

=

5.0

,

side

=

BUY

,

token_id

=

""

,

#Token ID you want to purchase goes here. Example token: 114304586861386186441621124384163963092522056897081085884483958561365015034812 ( Xi Jinping out in 2025, YES side )

)

signed_order

=

client.create_order(order_args)

## GTC(Good-Till-Cancelled) Order

resp

=

client.post_order(signed_order, OrderType.

GTC

)

print

(resp)

See all 38 lines

​

In addition to detailed comments in the code snippet, here are some more tips to help you get started.

See the Python example for details on the proper way to initialize a Py-Clob-Client depending on your wallet type. Three exhaustive examples are given. If using a MetaMask wallet or EOA please see the resources

here

, for instructions on setting allowances.

When buying into a market you purchase a “Token” that token represents either a Yes or No outcome of the event. To easily get required token pairs for a given event we have provided an interactive endpoint

here

.

Common pitfalls:

Negrisk Markets require an additional flag in the OrderArgs

negrisk=False

invalid signature

error, likely due to one of the following.

Incorrect Funder and or Private Key

Incorrect NegRisk flag in your order arguments

not enough balance / allowance

.

Not enough USDC to perform the trade. See the formula at the bottom of

this

page for details.

If using Metamask / WEB3 wallet go

here

, for instructions on setting allowances.

Developer Quickstart

Glossary

⌘

I