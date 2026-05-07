# Selenium vs. Cypress in the Classroom: An Empirical Study of Teaching GUI Testing

> Replication package for the paper submitted to the **Education Track of the XXXIX Brazilian Symposium on Software Engineering (SBES 2026)**.

---

## Overview

This repository contains the replication package for an empirical study comparing **Cypress** and **Selenium** as introductory frameworks for GUI test automation in an undergraduate Software Verification and Validation course.

The study spans **five semesters** and involves **98 student pairs**, who developed GUI test suites for a web application using both frameworks under comparable conditions.We integrate static analysis of the generated test artifacts with questionnaire data to examine how the choice of framework affects both the structural quality of tests produced by students and their development experience
### Research Questions

- **RQ1:** How do Cypress and Selenium test suites written by undergraduate students compare in terms of quality?
- **RQ2:** How do students perceive the development experience and challenges of using Cypress and Selenium?

---
Repository Structure

```
.
├── README.md
│
│
├── materials/
│   ├── activity.pdf             # Assignment given to student pairs
│   └── questionnaire.md        # Perception questionnaire (closed + open-ended questions)
│
├── scripts/
│   ├── ast-analysis/            # Custom AST-based parser for conformance, fragility, and hard-coded smells
│   │   ├── ast.py
│   │   └── README.md
│   └── eslint-config/           # ESLint configuration with Cypress and Mocha plugins for test smell detection
│       ├── eslint.config.js
│       └── README.md
│
├── test-suites/                    # Anonymized test suites per semester
│   │   ├── S1.zip
│   │   ├── S2.zip
│   │   ├── S3.zip
│   │   ├── S4.zip
│   │   └── S5.zip

│
└── data/
    ├── code-analysis-results.csv     # Static analysis output (conformance, fragility, test smells)
│   │   ├── S1.cvs
│   │   ├── S2.cvs
│   │   ├── S3.cvs
│   │   ├── S4.cvs
│   │   └── S5.cvs

    └── questionnaire-responses.csv   # Anonymized questionnaire responses per pair and semester
│   │   ├── S1.cvs
│   │   ├── S2.cvs
│   │   ├── S3.cvs
│   │   ├── S4.cvs
│   │   └── S5.cvs
```
---
## Study Design

| Item | Description |
|------|-------------|
| Course | Software Verification and Validation (undergraduate, CS program) |
| Participants | 98 pairs across 5 semesters (2023–2025) |
| Frameworks | Cypress and Selenium WebDriver |
| System Under Test | [Sylius](https://sylius.com/) — open-source eCommerce platform |
| Data collection | Test suite submissions + perception questionnaire |
| Analysis | AST-based static analysis + ESLint + content analysis of open-ended responses |

Each pair developed two test suites — one in Cypress, one in Selenium — targeting a specific Sylius feature. Minimum requirements: ≥ 10 test cases per suite, ≥ 4 GUI interactions per test case, ≥ 1 assertion per test case.

---

## Analysis Pipeline

Two complementary tools were used to extract metrics from the test suites:

**1. AST-based analysis** (`scripts/ast-analysis/`)  
Parses each test file into an Abstract Syntax Tree to extract: `test_case_count`, `assertion_conformity`, `interaction_conformity`, `avg_assertions`, `total_locators`, `fragile_locator_rate`, locator type breakdown (`loc_class`, `css_outro`, `xpath_relativo`), and the `smell_hard_coded` metric.

**2. ESLint** (`scripts/eslint-config/`)  
Detects the following test smells: `eslint_cy_wait_fixo`, `eslint_unsafe_chain`, `eslint_await_loop`, `eslint_no_only_test`, `eslint_no_unused_var`, `max_lines_per_function`, `max_statements`.

See each script's `README.md` for setup and usage instructions.

---

## Data Files

### `data/code-analysis-results.csv`

One row per pair per framework. Columns:

| Column | Description |
|--------|-------------|
| `semester` | S1–S5 |
| `pair_id` | Anonymized pair identifier |
| `framework` | `cypress` or `selenium` |
| `test_case_count` | Number of test cases (starter kit excluded) |
| `assertion_conformity` | % of test cases with ≥ 1 assertion |
| `interaction_conformity` | % of test cases with ≥ 4 interactions |
| `avg_assertions` | Average assertions per test case |
| `total_locators` | Total locators found in the suite |
| `fragile_locator_rate` | Line-weighted proportion of fragile locators |
| `loc_class` | Count of class-based locators |
| `css_outro` | Count of unclassified CSS locators |
| `xpath_relativo` | Count of relative XPath locators |
| `smell_hard_coded` | Hard-coded values smell count |
| `eslint_cy_wait_fixo` | Fixed-wait smell (ESLint) |
| `eslint_unsafe_chain` | Unsafe chain smell (ESLint) |
| `eslint_await_loop` | Await-loop smell (ESLint) |
| `eslint_no_only_test` | `.only()` smell (ESLint) |
| `eslint_no_unused_var` | Unused variable smell (ESLint) |
| `max_lines_per_function` | Max lines per function smell (ESLint) |
| `max_statements` | Max statements smell (ESLint) |

### `data/questionnaire-responses.csv`

One row per pair. Columns: `semester`, `pair_id`, `preferred_framework`, `used_capture_replay_cypress`, `corrected_cypress`, `used_capture_replay_selenium`, `corrected_selenium`, `sync_issues_cypress`, `sync_issues_selenium`, `open_response`.

---

## Ethical Considerations

Data was collected as part of regular course activities and anonymized prior to analysis. No personally identifiable information is included in this repository.

---

## License

MIT License
---

