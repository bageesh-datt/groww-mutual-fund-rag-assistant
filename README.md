# Groww Mutual Fund RAG Assistant

### A Source-Grounded AI Assistant for Mutual Fund FAQs

**Project Type:** AI Product / RAG-based Application  
**Domain:** FinTech | Mutual Funds  
**Focus:** Retrieval-Augmented Generation (RAG), factual Q&A, source citations and responsible AI.

[![Live Demo](https://img.shields.io/badge/Live-Demo-brightgreen)](https://lnkd.in/gp6Y7EjG)

---

## 1. Project Overview

The Groww Mutual Fund RAG Assistant is an AI-powered FAQ assistant designed to answer factual questions about mutual fund schemes using verified public information from official sources.

It helps users understand scheme-related information such as expense ratios, exit loads, minimum SIP amounts, ELSS lock-in periods, riskometers, benchmarks and statement download procedures.

The assistant uses a retrieval-based approach to provide source-grounded answers rather than generating unsupported financial information.

## 2. Problem Statement

Users often need to navigate multiple documents and official pages to find specific mutual fund information.

Finding accurate, scheme-specific details can be time-consuming, especially when information is spread across factsheets, scheme documents, FAQs and official guidance pages.

**Product Opportunity:** Build a simple FAQ assistant that makes official mutual fund information easier to access through natural-language questions.

## 3. Target Users

- Retail investors comparing mutual fund schemes.
- Users looking for factual information about mutual fund features.
- Support and content teams handling repetitive mutual fund queries.

## 4. Key Features

- **Factual Question Answering:** Answers questions about mutual fund scheme information.
- **Source-Based Retrieval:** Uses information from official public sources.
- **Source Citations:** Includes a relevant source link with every answer.
- **Safe Refusal:** Declines investment advice and opinion-based portfolio questions.
- **Concise Responses:** Keeps answers short and easy to understand.
- **Transparent Information:** Displays source update context where available.

## 5. Supported Query Categories

- Expense Ratio
- Exit Load
- Minimum SIP
- ELSS Lock-in Period
- Riskometer
- Scheme Benchmark
- Mutual Fund Statement Download
- Capital Gains Statement Guidance

## 6. RAG Architecture

The application follows a Retrieval-Augmented Generation workflow:

1. **Source Collection:** Collect public information from official AMC, SEBI and AMFI pages.
2. **Document Processing:** Prepare source documents for retrieval.
3. **Vector Storage:** Store the processed knowledge corpus for semantic retrieval.
4. **Query Processing:** Identify the user's factual question.
5. **Context Retrieval:** Retrieve relevant information from the knowledge base.
6. **Answer Generation:** Generate a concise answer grounded in retrieved information.
7. **Citation:** Attach the relevant source link to the answer.
8. **Safety Handling:** Refuse investment advice and unsupported questions.

## 7. Safety & Responsible AI

The assistant follows a facts-only approach.

- Uses official public sources.
- Does not provide investment recommendations.
- Does not calculate or compare investment returns.
- Refuses buy/sell or portfolio advice questions.
- Does not collect or store sensitive personal information.
- Provides source links to support factual responses.

**Disclaimer:** This assistant provides educational information only. It does not provide investment advice.

## 8. Technology & Project Structure

The repository is organised into the following components:

- `api/` – API-related components
- `backend/` – Backend application
- `frontend/` – User interface
- `data/vector_db/` – Vector database and knowledge corpus
- `docs/` – Project documentation
- `evaluation/` – Evaluation resources
- `scripts/` – Supporting scripts

Additional project files include implementation documentation, problem statement, requirements and deployment configuration.

## 9. Project Resources

- **GitHub Repository:** https://github.com/bageesh-datt/groww-mutual-fund-rag-assistant
- **Live Prototype / Demo:** https://lnkd.in/gp6Y7EjG

## 10. Project Objective

To make reliable mutual fund information easier to access through a conversational interface while maintaining factual accuracy, source transparency and responsible AI boundaries.

---

## Project Status

A deployed project with a public GitHub repository.

**Note:** This is an independent project and is not an official Groww product or an official Groww application.
