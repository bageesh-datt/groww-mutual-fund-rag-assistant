**Build a RAG Chatbot - Problem statement**

### Problem Statement

Problem Statement: Mutual Fund FAQ Assistant (Facts-Only Q&A)  
Overview

The objective of this project is to build a **facts-only FAQ assistant** for mutual fund schemes, using **Groww** as the reference product context. The assistant will answer **objective, verifiable queries** related to mutual funds by retrieving information exclusively from the **5 designated Groww mutual fund scheme web pages** (HTML web content only; no PDFs).

The system must strictly **avoid providing investment advice, opinions, or recommendations**. Every response must include a **single, clear source link** and adhere to defined constraints around clarity, accuracy, and compliance.

---

Objective

Design and implement a lightweight **Retrieval-Augmented Generation (RAG)-based assistant** that:

* Answers **factual queries** about mutual fund schemes  
* Uses a **curated corpus of 5 specific Groww mutual fund scheme URLs (HTML web content only, no PDFs)**  
* Provides **concise, source-backed responses**

---

Target Users

* Retail investors comparing mutual fund schemes  
* Customer support and content teams handling repetitive mutual fund queries

---

Scope of Work

1. Corpus Definition

* **Exclusive Scope (5 Scheme URLs Only):** Data ingestion is strictly limited to HTML content scraped from the following 5 Groww scheme URLs:
  * `https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth`
  * `https://groww.in/mutual-funds/hdfc-silver-etf-fof-direct-growth`
  * `https://groww.in/mutual-funds/hdfc-defence-fund-direct-growth`
  * `https://groww.in/mutual-funds/hdfc-equity-fund-direct-growth`
  * `https://groww.in/mutual-funds/hdfc-small-cap-fund-direct-growth`
* **No PDFs:** No PDF documents (such as KIM, SID, factsheets, or regulatory PDFs) will be collected, ingested, or processed. Data sources are strictly HTML web pages.

---

2. FAQ Assistant Requirements

The assistant must:

* Answer **facts-only queries**, such as:  
  * Expense ratio of a scheme  
  * Exit load details  
  * Minimum SIP amount  
  * Riskometer classification  
  * Benchmark index  
* Ensure:  
  * Each response is **limited to a maximum of 3 sentences**  
  * Each response includes **exactly one citation link**  
  * Each response includes a footer:  
     **“Last updated from sources: <date>”**

---

3. Refusal Handling

The assistant must **refuse non-factual or advisory queries**, such as:

* “Should I invest in this fund?”  
* “Which fund is better?”

Refusal responses should:

* Be **polite and clearly worded**  
* Reinforce the **facts-only limitation**  
* Provide a **relevant official scheme page link**

---

4. User Interface (Minimal)

The solution should include a simple interface with:

* A welcome message  
* Three example questions  
* A visible disclaimer:  
   **“Facts-only. No investment advice.”**

---

Constraints

Data and Sources

* Ingest data **strictly from the 5 specified Groww URLs** (HTML web content only)
* **No PDFs:** Exclude all PDF files (KIM, SID, factsheet PDFs, etc.)
* Do **not** use third-party blogs or aggregator websites

Privacy and Security

* Do **not** collect, store, or process:  
  * PAN or Aadhaar numbers  
  * Account numbers  
  * OTPs  
  * Email addresses or phone numbers

Content Restrictions

* No investment advice or recommendations  
* No performance comparisons or return calculations  
* For performance-related queries, provide a **link to the official scheme page only**

Transparency

* Responses must be **short, factual, and verifiable**  
* Every answer must include a **source link and last updated date**

---

Expected Deliverables

1. **README Document**  
   * Setup instructions  
   * Selected AMC and schemes  
   * Architecture overview (RAG approach)  
   * Known limitations  
2. **Disclaimer Snippet**  
   * “Facts-only. No investment advice.”

---

Success Criteria

* Accurate retrieval of factual mutual fund information  
* Strict adherence to **facts-only responses**  
* Consistent inclusion of **valid source citations**  
* Proper refusal of advisory queries  
* Clean, minimal, and user-friendly interface

---

Summary

The goal is to build a **trustworthy, transparent, and compliant mutual fund FAQ assistant** that prioritizes **accuracy over intelligence**. The system should ensure that users receive only **verified, source-backed financial information**, without any advisory bias or speculative content.