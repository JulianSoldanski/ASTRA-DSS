# ASTRA-DSS: B2B Procurement Decision Support System

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Status: Development](https://img.shields.io/badge/Status-In%20Development-orange)]()

**ASTRA-DSS** is an AI-driven Decision Support System (DSS) designed to empower B2B buyers and procurement professionals to make mathematically optimal negotiation decisions. By combining game theory mechanics with advanced Large Language Models (LLMs), ASTRA-DSS provides strategic, real-time guidance in complex supplier negotiations.

*This project is a specialized adaptation of the [ASTRA-NegoAgent framework](https://github.com/DSincerity/ASTRA-NegoAgent).*

## 🎯 The Vision
B2B procurement negotiations involve complex variables, shifting priorities, and incomplete information. ASTRA-DSS acts as a strategic co-pilot for buyers. It analyzes the negotiation context, predicts supplier behavior, and suggests optimized offers that maximize value while maintaining healthy business relationships.

## 💡 Key Features

* **Game-Theoretic Strategy:** Employs advanced strategic modeling to balance distributive (value-claiming) and integrative (value-creating) negotiation tactics.
* **Supplier Behavior Modeling:** Dynamically assesses and adapts to the counterparty's likely priorities and acceptance probabilities.
* **Optimal Offer Generation:** Integrates mathematical optimization (Linear Programming) to calculate and suggest the exact parameters for the next best counter-offer.
* **Strategic Reasoning Engine:** Powered by state-of-the-art LLMs (GPT-4o, Claude 3.5, Gemini) to understand nuanced business dialogue and context.

## 🚀 Getting Started

### Prerequisites
* **Python**: 3.10+
* **API Keys**: Access to OpenAI, Anthropic, or Google Gemini APIs depending on the chosen reasoning engine.

### Installation

```bash
# Clone the repository
git clone [https://github.com/JulianSoldanski/ASTRA-DSS.git](https://github.com/JulianSoldanski/ASTRA-DSS.git)
cd ASTRA-DSS

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
