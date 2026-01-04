# How to Fetch Markets - Polymarket Documentation

URL: https://docs.polymarket.com/developers/gamma-markets-api/fetch-markets-guide

---

How to Fetch Markets - Polymarket Documentation

Skip to main content

Polymarket Documentation

home page

Search...

⌘

K

Search...

Navigation

Gamma Structure

How to Fetch Markets

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

1. Fetch by Slug

How to Extract the Slug

API Endpoints

Examples

2. Fetch by Tags

Discover Available Tags

Using Tags in Market Requests

Additional Tag Filtering

3. Fetch All Active Markets

Key Parameters

Examples

Pagination

Best Practices

Related Endpoints

Both the getEvents and getMarkets are paginated. See

pagination section

for details.

This guide covers the three recommended approaches for fetching market data from the Gamma API, each optimized for different use cases.

​

Overview

There are three main strategies for retrieving market data:

By Slug

- Best for fetching specific individual markets or events

By Tags

- Ideal for filtering markets by category or sport

Via Events Endpoint

- Most efficient for retrieving all active markets

​

1. Fetch by Slug

Use Case:

When you need to retrieve a specific market or event that you already know about.

Individual markets and events are best fetched using their unique slug identifier. The slug can be found directly in the Polymarket frontend URL.

​

How to Extract the Slug

From any Polymarket URL, the slug is the path segment after

/event/

or

/market/

:

Copy

Ask AI

https://polymarket.com/event/fed-decision-in-october?tid=1758818660485

↑

Slug: fed-decision-in-october

​

API Endpoints

For Events:

GET /events/slug/

For Markets:

GET /markets/slug/

​

Examples

Copy

Ask AI

curl

"https://gamma-api.polymarket.com/events/slug/fed-decision-in-october"

​

2. Fetch by Tags

Use Case:

When you want to filter markets by category, sport, or topic.

Tags provide a powerful way to categorize and filter markets. You can discover available tags and then use them to filter your market requests.

​

Discover Available Tags

General Tags:

GET /tags

Sports Tags & Metadata:

GET /sports

The

/sports

endpoint returns comprehensive metadata for sports including tag IDs, images, resolution sources, and series information.

​

Using Tags in Market Requests

Once you have tag IDs, you can use them with the

tag_id

parameter in both markets and events endpoints.

Markets with Tags:

GET /markets

Events with Tags:

GET /events

Copy

Ask AI

curl

"https://gamma-api.polymarket.com/events?tag_id=100381&limit=1&closed=false"

​

Additional Tag Filtering

You can also:

Use

related_tags=true

to include related tag markets

Exclude specific tags with

exclude_tag_id

​

3. Fetch All Active Markets

Use Case:

When you need to retrieve all available active markets, typically for broader analysis or market discovery.

The most efficient approach is to use the

/events

endpoint and work backwards, as events contain their associated markets.

Events Endpoint:

GET /events

Markets Endpoint:

GET /markets

​

Key Parameters

order=id

- Order by event ID

ascending=false

- Get newest events first

closed=false

- Only active markets

limit

- Control response size

offset

- For pagination

​

Examples

Copy

Ask AI

curl

"https://gamma-api.polymarket.com/events?order=id&ascending=false&closed=false&limit=100"

This approach gives you all active markets ordered from newest to oldest, allowing you to systematically process all available trading opportunities.

​

Pagination

For large datasets, use pagination with

limit

and

offset

parameters:

limit=50

- Return 50 results per page

offset=0

- Start from the beginning (increment by limit for subsequent pages)

Pagination Examples:

Copy

Ask AI

# Page 1: First 50 results (offset=0)

curl

"https://gamma-api.polymarket.com/events?order=id&ascending=false&closed=false&limit=50&offset=0"

Copy

Ask AI

# Page 2: Next 50 results (offset=50)

curl

"https://gamma-api.polymarket.com/events?order=id&ascending=false&closed=false&limit=50&offset=50"

Copy

Ask AI

# Page 3: Next 50 results (offset=100)

curl

"https://gamma-api.polymarket.com/events?order=id&ascending=false&closed=false&limit=50&offset=100"

Copy

Ask AI

# Paginating through markets with tag filtering

curl

"https://gamma-api.polymarket.com/markets?tag_id=100381&closed=false&limit=25&offset=0"

Copy

Ask AI

# Next page of markets with tag filtering

curl

"https://gamma-api.polymarket.com/markets?tag_id=100381&closed=false&limit=25&offset=25"

​

Best Practices

For Individual Markets:

Always use the slug method for best performance

For Category Browsing:

Use tag filtering to reduce API calls

For Complete Market Discovery:

Use the events endpoint with pagination

Always Include

closed=false

:

Unless you specifically need historical data

Implement Rate Limiting:

Respect API limits for production applications

​

Related Endpoints

Get Markets

- Full markets endpoint documentation

Get Events

- Full events endpoint documentation

Search Markets

- Search functionality

Gamma Structure

Health check

⌘

I