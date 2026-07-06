# Selenium vs. Cypress in the Classroom: A Multi-Semester Case Study on GUI Test Quality and Student Experience


---

## Overview
This repository provides the replication package for a multi-semester classroom case study comparing Cypress and Selenium as introductory frameworks for GUI test automation in an undergraduate software quality course.

The study investigates how the choice of testing framework influences both the structural quality of student-produced test artifacts and the development experience perceived by novice testers. Across five semesters, 98 student pairs developed GUI test suites for the same web application using both frameworks under comparable instructional conditions.

The replication package includes the materials, data, and analysis scripts used to examine the resulting test suites through a static analysis pipeline focused on conformance, locator fragility, and test smells. It also includes questionnaire data collected to understand students’ perceptions of usability, challenges, debugging support, synchronization, and overall development experience.

By combining artifact-based analysis with students’ self-reported perceptions, the study provides empirical evidence on the trade-offs between Cypress and Selenium and supports more informed decisions about framework selection in introductory software testing and software quality courses.
### Research Questions

- **RQ1:** How do Cypress and Selenium test suites written by undergraduate students compare in terms of quality?
- **RQ2:** How do students perceive the development experience and challenges of using Cypress and Selenium?

---

## Repository Structure

```
.
├── README.md
│
├── materials/
│   ├── activity.pdf            # Assignment given to student pairs
│   └── questionnaire.md        # Perception questionnaire (closed + open-ended questions - In portuguese)
|   └── startetkit.zip          # Starter kit provided

│
├── scripts/
│   ├── ast-analysis/            # Custom AST-based parser for conformance, fragility, and hard-coded smells
│     ├── ast.py
│     └── README.md
│   └── eslint-config/           # ESLint configuration with Cypress and Mocha plugins for test smell detection
│       ├── eslint.config.js
│       └── README.md
|   └── statistical-analysis/    # Script for statistical analysis
│       ├── wilcoson.py
│       
│
├── test-suites/                 # Anonymized test suites per semester
│   ├── S1.zip
│   ├── S2.zip
│   ├── S3.zip
│   ├── S4.zip
│   └── S5.zip
│
└── data/
    ├── code-analysis-results.csv     # Static analysis output (conformance, fragility, test smells)
    │   ├── S1.csv
    │   ├── S2.csv
    │   ├── S3.csv
    │   ├── S4.csv
    │   └── S5.csv
    └── questionnaire-responses.csv   # Anonymized questionnaire responses per pair and semester (in Portuguese)
        ├── S1.csv
        ├── S2.csv
        ├── S3.csv
        ├── S4.csv
        └── S5.csv
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

Students received a starter kit with a preconfigured Docker container and one reference test case for each framework (Cypress and Selenium). The examples targeted the assigned administrative-panel section and were included in the submissions.

---

## Analysis Pipeline

### 1. AST-based analysis (`scripts/ast-analysis/`)
Parses each test file into an Abstract Syntax Tree to extract:

- test_case_count  
- assertion_conformity  
- interaction_conformity  
- avg_assertions  
- total_locators  
- fragile_locator_rate  
- locator breakdown  
- smell_hard_coded  

---

### 2. ESLint (`scripts/eslint-config/`)
Detects test smells such as:

- fixed waits  
- unsafe chains  
- await loops  
- `.only()` usage  
- unused variables  
- max lines per function  
- max statements  

---

### 3. Statistical analysis (`scripts/statistical-analysis/`)
Applies the Wilcoxon Signed-Rank test to validate differences between Cypress and Selenium across all metric groups: Group 1 (test_case_count, assertion_conformity, interaction_conformity), Group 2 (fragile_locator_rate, avg_assertions), and Group 3 (test smells). Reports W statistic, p-value, and rank-biserial effect size r overall and per semester.

---

## Data Files

### `data/code-analysis-results.csv`

One row per pair per framework:

| Column | Description |
|--------|-------------|
| semester | S1–S5 |
| pair_id | Anonymized pair identifier |
| framework | cypress / selenium |
| test_case_count | Number of test cases (starter kit excluded) |
| assertion_conformity | % of test cases with ≥ 1 assertion |
| interaction_conformity | % of test cases with ≥ 4 interactions |
| avg_assertions | Average assertions per test case |
| total_locators | Total locators found in the suite |
| fragile_locator_rate | Line-weighted proportion of fragile locators |
| loc_class | Count of class-based locators |
| css_outro | Count of unclassified CSS locators |
| xpath_relativo | Count of relative XPath locators |
| smell_hard_coded | Hard-coded values smell count |
| eslint_cy_wait_fixo | Fixed-wait smell (ESLint) |
| eslint_unsafe_chain | Unsafe chain smell (ESLint) |
| eslint_await_loop | Await-loop smell (ESLint) |
| eslint_no_only_test | `.only()` smell (ESLint) |
| eslint_no_unused_var | Unused variable smell (ESLint) |
| max_lines_per_function | Max lines per function smell (ESLint) |
| max_statements | Max statements smell (ESLint) |

---

### `data/questionnaire-responses.csv`

One row per pair:

- semester  
- pair_id  
- preferred_framework  
- used_capture_replay_cypress  
- corrected_cypress  
- used_capture_replay_selenium  
- corrected_selenium  
- sync_issues_cypress  
- sync_issues_selenium  
- open_response  

> **Note:** Open-ended responses are in Portuguese.

---

## Ethical Considerations

Data was collected as part of regular course activities and anonymized prior to analysis. No personally identifiable information is included in this repository.

---

## License

MIT License

>>>>>>> 5154717 (feat. questionare)
