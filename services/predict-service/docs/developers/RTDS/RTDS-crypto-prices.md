# RTDS Crypto Prices - Polymarket Documentation

URL: https://docs.polymarket.com/developers/RTDS/RTDS-crypto-prices

---

RTDS Crypto Prices - Polymarket Documentation

Skip to main content

Polymarket Documentation

home page

Search...

⌘

K

Search...

Navigation

Real Time Data Stream

RTDS Crypto Prices

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

Binance Source (crypto_prices)

Subscription Details

Subscription Message

With Symbol Filter

Chainlink Source (crypto_prices_chainlink)

Subscription Details

Subscription Message

With Symbol Filter

Message Format

Binance Source Message Format

Chainlink Source Message Format

Payload Fields

Example Messages

Binance Source Examples

Solana Price Update (Binance)

Bitcoin Price Update (Binance)

Chainlink Source Examples

Ethereum Price Update (Chainlink)

Bitcoin Price Update (Chainlink)

Supported Symbols

Binance Source Symbols

Chainlink Source Symbols

Notes

General

Polymarket provides a Typescript client for interacting with this streaming service.

Download and view it’s documentation here

​

Overview

The crypto prices subscription provides real-time updates for cryptocurrency price data from two different sources:

Binance Source

(

crypto_prices

): Real-time price data from Binance exchange

Chainlink Source

(

crypto_prices_chainlink

): Price data from Chainlink oracle networks

Both streams deliver current market prices for various cryptocurrency trading pairs, but use different symbol formats and subscription structures.

​

Binance Source (

crypto_prices

)

​

Subscription Details

Topic

:

crypto_prices

Type

:

update

Authentication

: Not required

Filters

: Optional (specific symbols can be filtered)

Symbol Format

: Lowercase concatenated pairs (e.g.,

solusdt

,

btcusdt

)

​

Subscription Message

Copy

Ask AI

{

"action"

:

"subscribe"

,

"subscriptions"

: [

{

"topic"

:

"crypto_prices"

,

"type"

:

"update"

}

]

}

​

With Symbol Filter

To subscribe to specific cryptocurrency symbols, include a filters parameter:

Copy

Ask AI

{

"action"

:

"subscribe"

,

"subscriptions"

: [

{

"topic"

:

"crypto_prices"

,

"type"

:

"update"

,

"filters"

:

"solusdt,btcusdt,ethusdt"

}

]

}

​

Chainlink Source (

crypto_prices_chainlink

)

​

Subscription Details

Topic

:

crypto_prices_chainlink

Type

:

*

(all types)

Authentication

: Not required

Filters

: Optional (JSON object with symbol specification)

Symbol Format

: Slash-separated pairs (e.g.,

eth/usd

,

btc/usd

)

​

Subscription Message

Copy

Ask AI

{

"action"

:

"subscribe"

,

"subscriptions"

: [

{

"topic"

:

"crypto_prices_chainlink"

,

"type"

:

"*"

,

"filters"

:

""

}

]

}

​

With Symbol Filter

To subscribe to specific cryptocurrency symbols, include a JSON filters parameter:

Copy

Ask AI

{

"action"

:

"subscribe"

,

"subscriptions"

: [

{

"topic"

:

"crypto_prices_chainlink"

,

"type"

:

"*"

,

"filters"

:

"{

\"

symbol

\"

:

\"

eth/usd

\"

}"

}

]

}

​

Message Format

​

Binance Source Message Format

When subscribed to Binance crypto prices (

crypto_prices

), you’ll receive messages with the following structure:

Copy

Ask AI

{

"topic"

:

"crypto_prices"

,

"type"

:

"update"

,

"timestamp"

:

1753314064237

,

"payload"

: {

"symbol"

:

"solusdt"

,

"timestamp"

:

1753314064213

,

"value"

:

189.55

}

}

​

Chainlink Source Message Format

When subscribed to Chainlink crypto prices (

crypto_prices_chainlink

), you’ll receive messages with the following structure:

Copy

Ask AI

{

"topic"

:

"crypto_prices_chainlink"

,

"type"

:

"update"

,

"timestamp"

:

1753314064237

,

"payload"

: {

"symbol"

:

"eth/usd"

,

"timestamp"

:

1753314064213

,

"value"

:

3456.78

}

}

​

Payload Fields

Field

Type

Description

symbol

string

Trading pair symbol

Binance

: lowercase concatenated (e.g., “solusdt”, “btcusdt”)

Chainlink

: slash-separated (e.g., “eth/usd”, “btc/usd”)

timestamp

number

Price timestamp in Unix milliseconds

value

number

Current price value in the quote currency

​

Example Messages

​

Binance Source Examples

​

Solana Price Update (Binance)

Copy

Ask AI

{

"topic"

:

"crypto_prices"

,

"type"

:

"update"

,

"timestamp"

:

1753314064237

,

"payload"

: {

"symbol"

:

"solusdt"

,

"timestamp"

:

1753314064213

,

"value"

:

189.55

}

}

​

Bitcoin Price Update (Binance)

Copy

Ask AI

{

"topic"

:

"crypto_prices"

,

"type"

:

"update"

,

"timestamp"

:

1753314088421

,

"payload"

: {

"symbol"

:

"btcusdt"

,

"timestamp"

:

1753314088395

,

"value"

:

67234.50

}

}

​

Chainlink Source Examples

​

Ethereum Price Update (Chainlink)

Copy

Ask AI

{

"topic"

:

"crypto_prices_chainlink"

,

"type"

:

"update"

,

"timestamp"

:

1753314064237

,

"payload"

: {

"symbol"

:

"eth/usd"

,

"timestamp"

:

1753314064213

,

"value"

:

3456.78

}

}

​

Bitcoin Price Update (Chainlink)

Copy

Ask AI

{

"topic"

:

"crypto_prices_chainlink"

,

"type"

:

"update"

,

"timestamp"

:

1753314088421

,

"payload"

: {

"symbol"

:

"btc/usd"

,

"timestamp"

:

1753314088395

,

"value"

:

67234.50

}

}

​

Supported Symbols

​

Binance Source Symbols

The Binance source supports various cryptocurrency trading pairs using lowercase concatenated format:

btcusdt

- Bitcoin to USDT

ethusdt

- Ethereum to USDT

solusdt

- Solana to USDT

xrpusdt

- XRP to USDT

​

Chainlink Source Symbols

The Chainlink source supports cryptocurrency trading pairs using slash-separated format:

btc/usd

- Bitcoin to USD

eth/usd

- Ethereum to USD

sol/usd

- Solana to USD

xrp/usd

- XRP to USD

​

Notes

​

General

Price updates are sent as market prices change

The timestamp in the payload represents when the price was recorded

The outer timestamp represents when the message was sent via WebSocket

No authentication is required for crypto price data

RTDS Overview

RTDS Comments

⌘

I