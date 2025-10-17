# **ADK Financial Advisor Agent: A Case Study in AI Systems Safety Engineering**

## **Introduction: A Praxis-Oriented Approach to AI Safety**

This repository contains the source code for the Financial Advisor Agent, a sample project built using Google's **Agent Development Kit (ADK)**.1 However, its primary purpose extends beyond a simple demonstration of agentic capabilities. This agent serves as the foundational capstone project for **"The Google AI Systems Safety Engineer: A Praxis-Oriented Professional Development Framework."** 1

The core philosophy of that program is "praxis"—learning through applied mastery.1 This codebase is not a finished product but a **baseline system** designed to be systematically analyzed, hardened, and transformed into a verifiably safe agent. The goal is not merely to build a functional financial advisor, but to use it as a live testbed for engineering a defensible, auditable safety case against the novel risks introduced by autonomous AI.1

**Disclaimer:** This is not an officially supported Google product. This project is intended for educational and research purposes in the field of AI systems safety. It is not intended for use in a production environment or for providing actual financial advice.

## **The Safety Engineering Lifecycle**

Working with this agent involves a cumulative, multi-stage process that mirrors a rigorous safety engineering lifecycle. The developer will apply formal methodologies to progressively enhance the agent's safety posture, culminating in a comprehensive safety case.

This repository is the starting point for a journey that explores several critical AI safety concepts:

* **A Taxonomy of Autonomy-Induced Risks:** The agent serves as a practical environment to demonstrate and mitigate novel, autonomy-specific threats such as **Memory Poisoning**, **Reward Hacking (Specification Gaming)**, **Unsafe Actuation**, and **Emergent Deception**.1  
* **Model-Based Systems Engineering (MBSE):** The initial phase of the curriculum involves creating a formal MBSE model of this agent's architecture and behavior using SysML. This establishes a "single source of truth" for requirements, architecture, and safety analysis.1  
* **Operational Safety and Governance:** The agent is the subject of a formal hazard analysis based on methodologies like **MIL-STD 882E**. This analysis informs the design of a comprehensive observability and governance plan using Google Cloud tools like **Model Armor** and **AI Protection** to monitor the agent in a simulated operational environment.2  
* **Formal Methods for Provably Safe Control:** The agent's default decision-making logic is designed to be replaced with a more formal, provably safe policy. This involves modeling the agent's behavior using **Markov Decision Processes (MDPs)** and implementing safety constraints using **Constrained MDPs (CMDPs)** and Safe Reinforcement Learning techniques.1  
* **Advanced Safety Architectures:** The final, hardened version of the agent incorporates multi-layered, defense-in-depth safety systems. This includes a **Reflective Engine** that forces the agent to critique its own proposed actions against a "constitution" of immutable safety principles before execution.1  
* **Adversarial Testing and Red Teaming:** A key validation step involves conducting targeted red teaming exercises against the hardened agent to prove that the implemented safety measures are effective at mitigating the vulnerabilities demonstrated in earlier stages.4

## **Getting Started: Setting Up the Baseline Agent**

Follow these instructions to set up the initial, un-hardened version of the Financial Advisor Agent on your local machine.

### **Prerequisites**

* Python 3.9+  
* Git version control system  
* A configured Google Cloud project with billing enabled.  
* Authenticated Google Cloud CLI.

### **1\. Clone the Repository**

First, clone the adk-samples repository to your local machine:

Bash

git clone https://github.com/google/adk-samples.git  
cd adk-samples/python/agents/financial-advisor

### **2\. Set Up a Virtual Environment**

It is highly recommended to use a Python virtual environment to manage dependencies and avoid conflicts.

Bash

\# Create a virtual environment  
python \-m venv.venv

\# Activate the environment  
\# On macOS/Linux:  
source.venv/bin/activate  
\# On Windows (CMD):  
.venv\\Scripts\\activate.bat

### **3\. Install Dependencies**

Install the required Python packages, including the google-adk, using the requirements.txt file.

Bash

pip install \-r requirements.txt

### **4\. Configure Environment Variables**

The agent requires API keys and project configuration to function. Create a .env file in the agent's root directory (financial-advisor/).

Bash

touch.env

Open the .env file and add the following configuration. If you are using Gemini via Vertex AI, you will need to specify your Google Cloud project and location.

Code snippet

\# If using Gemini via Vertex AI on Google Cloud  
GOOGLE\_CLOUD\_PROJECT="your-gcp-project-id"  
GOOGLE\_CLOUD\_LOCATION="your-gcp-location" \# e.g., us-central1  
GOOGLE\_GENAI\_USE\_VERTEXAI="True"

\# If using Gemini API directly  
\# GOOGLE\_API\_KEY="your-gemini-api-key"

## **Running the Agent for Safety Analysis**

The ADK provides several ways to run and interact with your agent. Within the safety curriculum, these are used not for general-purpose chat but for targeted experiments to demonstrate vulnerabilities or validate mitigations.

### **Using the Web UI (Recommended for Analysis)**

The ADK includes a built-in web interface that is excellent for testing, debugging, and visualizing the agent's step-by-step reasoning process. This is critical for analyzing the agent's behavior during safety exercises.

From within the financial-advisor directory, run the following command:

Bash

adk web

Navigate to http://localhost:8000 in your browser. Use this interface to conduct experiments like the **Memory Poisoning** attack and observe the agent's internal state and tool calls.1

### **Using the Command Line**

For quick tests, you can run the agent directly from your terminal.

Bash

adk run

## **The Agent's Transformation Journey**

The core of the work with this repository is to execute the "Praxis Projects" outlined in the AI Systems Safety Engineer framework. This involves:

1. **Praxis Project 1:** Creating a formal MBSE model of the baseline agent's architecture, behavior, and requirements.1  
2. **Praxis Project 2:** Adding a persistent memory capability and then executing a targeted **Memory Poisoning** attack to demonstrate the resulting vulnerability.1  
3. **Praxis Project 3:** Conducting a formal hazard analysis (PHA/FMEA) and designing a technical observability and security plan using Google Cloud's AI Protection and Model Armor.1  
4. **Praxis Project 4:** Re-implementing the agent's decision-making core using a **POMDP** for state estimation and a **CMDP** to enforce hard safety constraints.1  
5. **Praxis Project 5 (Capstone):** Integrating all safety components into a final, multi-layered architecture and conducting a final red team evaluation to prove the mitigation of the memory poisoning threat.1

## **Final Objective: The Praxis Paper**

The ultimate goal of this project is to produce a comprehensive **Praxis Paper**. This document will present the final, hardened architecture, the formal safety model, and an evaluation that includes a **Threat-Mitigation Traceability Matrix**. This matrix serves as the auditable safety case, providing a defensible argument that the agent is acceptably safe for its intended (simulated) use case.1

## **Contributing**

Contributions from the community are welcome\! Please see the CONTRIBUTING.md file for guidelines on how to contribute to this project.

## **License**

This project is licensed under the Apache 2.0 License. See the LICENSE file for more details.

#### **Works cited**

1. The AI Systems Safety Engineer: A Praxis-Oriented Self-Study Program  
2. Securing AI | Google Cloud, accessed October 17, 2025, [https://cloud.google.com/security/securing-ai](https://cloud.google.com/security/securing-ai)  
3. Security in AI Era: Protecting AI Workloads with Google Cloud \- Cyber Defense Magazine, accessed October 17, 2025, [https://www.cyberdefensemagazine.com/security-in-ai-era-protecting-ai-workloads-with-google-cloud/](https://www.cyberdefensemagazine.com/security-in-ai-era-protecting-ai-workloads-with-google-cloud/)  
4. Google introduces AI Red Team \- Google Blog, accessed October 17, 2025, [https://blog.google/technology/safety-security/googles-ai-red-team-the-ethical-hackers-making-ai-safer/](https://blog.google/technology/safety-security/googles-ai-red-team-the-ethical-hackers-making-ai-safer/)
