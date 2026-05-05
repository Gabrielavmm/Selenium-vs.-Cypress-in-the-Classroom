# Selenium vs. Cypress in the Classroom: An Empirical Study of Teaching GUI Testing

> Replication package for the paper submitted to the **Education Track of the XXXIX Brazilian Symposium on Software Engineering (SBES 2026)**.

---

## Overview

This repository contains the replication package for an empirical study comparing **Cypress** and **Selenium** as introductory frameworks for GUI test automation in an undergraduate Software Verification and Validation course.

The study spans **five semesters (2023–2025)** and involves **98 student pairs (196 students total)**, who developed GUI test suites for a real-world web application using both frameworks under comparable conditions. We combine static analysis of the resulting artifacts with questionnaire data to investigate how framework choice influences both the structural quality of student-produced tests and students' development experience.

### Research Questions

- **RQ1:** How do Cypress and Selenium test suites written by undergraduate students compare in terms of quality?
- **RQ2:** How do students perceive the development experience and challenges of using Cypress and Selenium?

---

## Repository Structure

```
.
├── README.md
│
├── study-design/
│   └── study-design.md          # Study goals, context, protocol, and metrics description
│
├── materials/
│   ├── activity.pdf             # Assignment given to student pairs
│   └── questionnaire.pdf        # Perception questionnaire (closed + open-ended questions)
│
├── scripts/
│   ├── ast-analysis/            # Custom AST-based parser for conformance, fragility, and hard-coded smells
│   │   ├── analyze.js
│   │   └── README.md
│   └── eslint-config/           # ESLint configuration with Cypress and Mocha plugins for test smell detection
│       ├── .eslintrc.json
│       └── README.md
│
├── test-suites/
│   ├── cypress/                 # Anonymized Cypress test suites per semester
│   │   ├── S1-cypress.zip
│   │   ├── S2-cypress.zip
│   │   ├── S3-cypress.zip
│   │   ├── S4-cypress.zip
│   │   └── S5-cypress.zip
│   └── selenium/                # Anonymized Selenium test suites per semester
│       ├── S1-selenium.zip
│       ├── S2-selenium.zip
│       ├── S3-selenium.zip
│       ├── S4-selenium.zip
│       └── S5-selenium.zip
│
└── data/
    ├── code-analysis-results.csv     # Static analysis output (conformance, fragility, test smells)
    └── questionnaire-responses.csv   # Anonymized questionnaire responses per pair and semester
```

---

## Study Design Summary

| Item | Description |
|---|---|
| **Course** | Software Verification and Validation (undergraduate) |
| **Participants** | 98 pairs (196 students) across 5 semesters |
| **Frameworks** | Cypress and Selenium (WebDriver) |
| **System Under Test** | [Sylius](https://sylius.com/) — open-source eCommerce platform |
| **Data Collection** | Test suite submissions + perception questionnaire |
| **Analysis** | Static analysis pipeline (AST + ESLint) + content analysis of open-ended responses |

Each pair was required to develop two test suites — one in Cypress and one in Selenium — targeting a specific feature of Sylius. Minimum requirements included at least 10 test cases per suite, 4 GUI interactions per test case, and at least 1 assertion per test case.

For full details on the study protocol, metrics definition, and data collection procedure, see [`study-design/study-design.md`](study-design/study-design.md).

---

## Artifacts

### Materials (`materials/`)

- **`activity.pdf`** — The assignment specification given to student pairs, including the testing objectives, minimum requirements, and submission instructions.
- **`questionnaire.pdf`** — The structured questionnaire administered at the end of the activity. It includes closed questions on framework preference, capture-replay usage, and synchronization challenges, as well as an open-ended question on perceived differences and difficulties.

### Analysis Scripts (`scripts/`)

Two complementary tools were used to analyze the test suites:

1. **AST-based analysis** (`scripts/ast-analysis/`): A custom JavaScript script that parses each test file into an Abstract Syntax Tree to extract conformance metrics (test case count, assertion conformity, interaction conformity), locator types and fragility rates, and the `hard_coded` test smell. AST parsing was preferred over text matching to avoid false positives from method names or comments.

2. **ESLint configuration** (`scripts/eslint-config/`): An ESLint setup using the `eslint-plugin-cypress` and `eslint-plugin-mocha` plugins to detect the following test smells: `fixed_wait`, `await_loop`, `unsafe_chain`, `no_only_test`, `no_unused_var`, `max_lines_per_function`, and `max_statements`.

Each `README.md` inside the script folders documents dependencies and usage instructions.

### Test Suites (`test-suites/`)

Anonymized test suite submissions organized by framework and semester. All identifying information (student names, university references, email addresses) has been removed. Each `.zip` file contains the suite files submitted by each pair in that semester, named `pair-N/` (e.g., `pair-1/`, `pair-2/`).

### Data (`data/`)

- **`code-analysis-results.csv`** — Output of the static analysis pipeline. Each row corresponds to one test suite (one pair × one framework). Columns include all metrics described in the paper: `semester`, `pair_id`, `framework`, `test_case_count`, `assert_conformity`, `interact_conformity`, `avg_assertions`, `fragile_locator_rate`, and all test smell counts.
- **`questionnaire-responses.csv`** — Anonymized questionnaire responses. Each row corresponds to one pair. Columns include: `semester`, `pair_id`, `preferred_framework`, `used_capture_replay_cypress`, `corrected_cypress`, `used_capture_replay_selenium`, `corrected_selenium`, `sync_issues_cypress`, `sync_issues_selenium`, and `open_response`.

---

## Metrics Reference

### Group 1 — Conformance

| Metric | Description |
|---|---|
| `test_case_count` | Number of test cases implemented (minimum required: 10) |
| `assert_conformity` | Proportion of test cases containing at least one assertion |
| `interact_conformity` | Proportion of test cases containing at least four GUI interactions |

### Group 2 — Complexity and Locator Fragility

| Metric | Description |
|---|---|
| `avg_assertions` | Average number of assertions per test case |
| `fragile_locator_rate` | Line-weighted proportion of fragile locators (XPath, structural CSS, class-based, etc.) |

### Group 3 — Test Smells (10% trimmed mean)

| Metric | Description |
|---|---|
| `hard_coded` | Hard-coded literal values in test actions or assertions |
| `fixed_wait` | Fixed-time waits (e.g., `cy.wait(n)`, `sleep(n)`) |
| `await_loop` | Polling loops used as synchronization strategy |
| `unsafe_chain` | Unsafe chaining of asynchronous Cypress commands |
| `no_only_test` | Use of `.only()` left unintentionally in the suite |
| `no_unused_var` | Declared variables never referenced |
| `max_lines_per_function` | Test functions exceeding a line count threshold |
| `max_statements` | Excessive number of statements in a single function |

---

## Reproducing the Analysis

### Requirements

- Node.js ≥ 18
- npm ≥ 9

### Steps

```bash
# 1. Install dependencies
cd scripts/ast-analysis
npm install

# 2. Run the AST analysis on a test suite folder
node analyze.js --input ../../test-suites/cypress/S1-cypress/ --framework cypress

# 3. Run ESLint smell detection
cd ../eslint-config
npm install
npx eslint ../../test-suites/cypress/S1-cypress/ --format json > smells-S1-cypress.json
```

Output files will match the columns in `data/code-analysis-results.csv`. Each script's `README.md` provides detailed usage instructions and configuration options.

---

## Ethical Considerations

All student data was collected as part of regular course activities. Participation was part of the course requirements, and data was anonymized prior to analysis and publication. No personally identifiable information is included in this repository.

---

## License

The artifacts in this repository are made available for research and replication purposes under the [MIT License](LICENSE).
