# Real Time Data Socket - Polymarket Documentation

URL: https://docs.polymarket.com/developers/RTDS/RTDS-overview

---

Real Time Data Socket - Polymarket Documentation

Skip to main content

Polymarket Documentation

home page

Search...

⌘

K

Search...

Navigation

Real Time Data Stream

Real Time Data Socket

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

Connection Details

Authentication

Connection Management

Available Subscription Types

Message Structure

Subscription Management

Subscribe to Topics

Unsubscribe from Topics

Error Handling

​

Overview

The Polymarket Real-Time Data Socket (RTDS) is a WebSocket-based streaming service that provides real-time updates for various Polymarket data streams. The service allows clients to subscribe to multiple data feeds simultaneously and receive live updates as events occur on the platform.

Polymarket provides a Typescript client for interacting with this streaming service.

Download and view it’s documentation here

​

Connection Details

WebSocket URL

:

wss://ws-live-data.polymarket.com

Protocol

: WebSocket

Data Format

: JSON

​

Authentication

The RTDS supports two types of authentication depending on the subscription type:

CLOB Authentication

: Required for certain trading-related subscriptions

key

: API key

secret

: API secret

passphrase

: API passphrase

Gamma Authentication

: Required for user-specific data

address

: User wallet address

​

Connection Management

The WebSocket connection supports:

Dynamic Subscriptions

: Without disconnecting from the socket users can add, remove and modify topics and filters they are subscribed to.

Ping/Pong

: You should send PING messages (every 5 seconds ideally) to maintain connection

​

Available Subscription Types

Although this connection technically supports additional activity and subscription types, they are not fully supported at this time. Users are free to use them but there may be some unexpected behavior.

The RTDS currently supports the following subscription types:

Crypto Prices

- Real-time cryptocurrency price updates

Comments

- Comment-related events including reactions

​

Message Structure

All messages received from the WebSocket follow this structure:

Copy

Ask AI

{

"topic"

:

"string"

,

"type"

:

"string"

,

"timestamp"

:

"number"

,

"payload"

:

"object"

}

topic

: The subscription topic (e.g., “crypto_prices”, “comments”, “activity”)

type

: The message type/event (e.g., “update”, “reaction_created”, “orders_matched”)

timestamp

: Unix timestamp in milliseconds

payload

: Event-specific data object

​

Subscription Management

​

Subscribe to Topics

To subscribe to data streams, send a JSON message with this structure:

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

"topic_name"

,

"type"

:

"message_type"

,

"filters"

:

"optional_filter_string"

,

"clob_auth"

: {

"key"

:

"api_key"

,

"secret"

:

"api_secret"

,

"passphrase"

:

"api_passphrase"

},

"gamma_auth"

: {

"address"

:

"wallet_address"

}

}

]

}

​

Unsubscribe from Topics

To unsubscribe from data streams, send a similar message with

"action": "unsubscribe"

.

​

Error Handling

Connection errors will trigger automatic reconnection attempts

Invalid subscription messages may result in connection closure

Authentication failures will prevent successful subscription to protected topics

Market Channel

RTDS Crypto Prices

⌘

I