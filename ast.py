from pathlib import Path
import tree_sitter_javascript as tsjava
from tree_sitter import Language, Parser


# ─────────────────────────────────────────────────────────────
# CONFIGURATION
# Set the paths to the files you want to analyze.
# ─────────────────────────────────────────────────────────────

CYPRESS_FILE  = "cypress/e2e/section-name.cy.js"
SELENIUM_FILE = "selenium/e2e/section-name.js"


# ─────────────────────────────────────────────────────────────
# AST PARSER SETUP
# tree-sitter transforms JS source into a syntax tree where
# each node represents a syntactic element of the code.
# ─────────────────────────────────────────────────────────────

JS_LANGUAGE = Language(tsjava.language())
parser = Parser(JS_LANGUAGE)


# ─────────────────────────────────────────────────────────────
# TREE NAVIGATION HELPERS
# ─────────────────────────────────────────────────────────────

def parse_file(path):
    """
    Reads a JS file as bytes and builds the AST.
    Using bytes preserves exact character positions and avoids
    encoding issues with special characters in student files.
    """
    code_bytes = Path(path).read_bytes()
    tree = parser.parse(code_bytes)
    return tree, code_bytes


def get_node_text(node, code_bytes):
    """
    Extracts the text of a node using byte offsets.
    errors='replace' prevents crashes on invalid characters.
    """
    return code_bytes[node.start_byte:node.end_byte].decode('utf-8', errors='replace')


def find_nodes(node, node_type):
    """
    Recursively traverses the subtree rooted at `node` and
    collects all nodes of the given type (depth-first search).
    """
    results = []
    if node.type == node_type:
        results.append(node)
    for child in node.children:
        results.extend(find_nodes(child, node_type))
    return results


def get_function_name(call_node, code):
    """
    Returns the method name from a call expression.
    Handles both simple calls (identifier) and chained calls
    (member_expression), e.g. cy.get(...) → 'get'.
    """
    func = call_node.child_by_field_name('function')
    if func is None:
        return ""
    if func.type == 'member_expression':
        prop = func.child_by_field_name('property')
        if prop:
            return get_node_text(prop, code)
    if func.type == 'identifier':
        return get_node_text(func, code)
    return ""


def get_call_object(call_node, code):
    """
    Returns the receiver object of a call expression.
    e.g. cy.get(...) → 'cy', By.id(...) → 'By'.
    Used to filter framework-specific calls.
    """
    func = call_node.child_by_field_name('function')
    if func and func.type == 'member_expression':
        obj = func.child_by_field_name('object')
        if obj:
            return get_node_text(obj, code)
    return ""


def get_first_argument_text(call_node, code):
    """
    Returns the text of the first argument of a call expression.
    Supports plain strings, template strings, and nested calls.
    """
    args = call_node.child_by_field_name('arguments')
    if args is None:
        return ""
    for child in args.children:
        if child.type in ('string', 'template_string'):
            text = get_node_text(child, code)
            return text.strip('"\'`')
        if child.type == 'call_expression':
            return get_node_text(child, code)
    return ""


# ─────────────────────────────────────────────────────────────
# EXTRACTING it() AND beforeEach() BLOCKS
# ─────────────────────────────────────────────────────────────

def extract_tests(tree, code):
    """
    Traverses the AST looking for it('name', () => { ... }) calls.
    Uses continue to skip into nested its — avoids double-counting.
    Supports single quotes, double quotes, and backtick names.
    """

    def find_it_calls(node):
        results = []
        for child in node.children:
            if child.type == 'call_expression':
                name = get_function_name(child, code)
                if name == 'it':
                    results.append(child)
                    continue
            results.extend(find_it_calls(child))
        return results

    tests = []
    all_calls = find_it_calls(tree.root_node)

    for call in all_calls:
        args = call.child_by_field_name('arguments')
        if args is None or len(args.children) < 2:
            continue

        test_name = ""
        body_node = None

        for child in args.children:
            if child.type == 'string' and not test_name:
                raw = get_node_text(child, code)
                test_name = raw.strip('"\'` \t\n')
            elif child.type == 'template_string' and not test_name:
                raw = get_node_text(child, code)
                test_name = raw.strip('`').strip('"\'')
                if not test_name:
                    for sub in child.children:
                        if sub.type == 'string_fragment':
                            test_name = get_node_text(sub, code)
                            break
            elif child.type in ('arrow_function', 'function_expression'):
                body_node = child

        if test_name and body_node:
            tests.append({"name": test_name, "node": call, "body_node": body_node})

    return tests


def extract_before_each(tree, code):
    """
    Locates the beforeEach(() => { ... }) block.
    Represents the shared setup environment (login, navigation).
    Treated separately to avoid inflating individual test metrics.
    """
    all_calls = find_nodes(tree.root_node, 'call_expression')
    for call in all_calls:
        if get_function_name(call, code) == 'beforeEach':
            args = call.child_by_field_name('arguments')
            if args:
                for child in args.children:
                    if child.type in ('arrow_function', 'function_expression'):
                        return child
    return None


# ─────────────────────────────────────────────────────────────
# GROUP 1 & 2 — CONFORMANCE AND COMPLEXITY
# ─────────────────────────────────────────────────────────────

ACTIONS_CYPRESS = {
    'click', 'type', 'clear', 'select', 'check', 'uncheck',
    'scrollIntoView', 'visit', 'wait', 'focus', 'blur',
    'submit', 'trigger', 'dblclick', 'rightclick'
}

ACTIONS_SELENIUM = {
    'click', 'sendKeys', 'clear', 'submit', 'get',
    'sleep', 'selectByVisibleText', 'selectByValue', 'navigate'
}

ASSERTIONS_CYPRESS  = {'should', 'expect', 'assert', 'and'}
ASSERTIONS_SELENIUM = {'assert', 'strictEqual', 'deepEqual', 'ok', 'equal'}


def count_interactions(body_node, code, framework):
    """
    Counts interaction actions within a test body (it block only).
    beforeEach is excluded to avoid inflating per-test averages.
    """
    actions = ACTIONS_CYPRESS if framework == 'cypress' else ACTIONS_SELENIUM
    total = 0
    for call in find_nodes(body_node, 'call_expression'):
        if get_function_name(call, code) in actions:
            total += 1
    return total


def count_assertions(body_node, code, framework):
    """
    Counts assertion calls within a test body.
    Assertions are what distinguish a validating test from a
    script that merely executes actions without checking outcomes.
    """
    assertions = ASSERTIONS_CYPRESS if framework == 'cypress' else ASSERTIONS_SELENIUM
    total = 0
    for call in find_nodes(body_node, 'call_expression'):
        if get_function_name(call, code) in assertions:
            total += 1
    return total


# ─────────────────────────────────────────────────────────────
# LOCATOR CLASSIFICATION
# Locators that rely on DOM structure (CSS class, XPath, position)
# are classified as fragile: any layout change may break the test
# even if the tested behavior has not changed.
# ─────────────────────────────────────────────────────────────

def classify_cypress_selector(selector):
    """
    Classifies a Cypress CSS selector by stability level.
    Checks are ordered from most stable to most fragile.

    Stable      → id, data-* attributes (bound to element identity)
    Medium      → visible text (may break with i18n in Sylius)
    Fragile     → CSS class (styling refactors break tests)
    Most fragile→ css_structural: nth-child, nested tags with >
    """
    s = selector.strip()

    if s.startswith('#') or s.startswith('[id=') or s.startswith('[id '):
        return 'id'
    if '[data-' in s or 'getBy' in s or 'findByRole' in s:
        return 'atributo_data'
    if ':contains' in s:
        return 'texto'
    if (s.startswith('.') or s.startswith('[class') or
            '*[class' in s or s.startswith('*[')):
        return 'class'
    if ('nth-child' in s or 'nth-of-type' in s or
            ('>' in s and any(tag in s for tag in ['div', 'span', 'label', 'input']))):
        return 'css_estrutural'
    return 'css_outro'


def classify_selenium_locator(by_type, value):
    """
    Classifies a Selenium locator by its By strategy.
    Selenium tends to induce XPath (more verbose and fragile),
    while Cypress induces CSS selectors — a structural difference
    relevant to the framework comparison.
    """
    by_type = by_type.lower()

    if by_type == 'id':
        return 'id'
    if by_type in ('linktext', 'partiallinktext'):
        return 'link_text'
    if by_type == 'tagname':
        return 'tag_body' if value.strip().lower() == 'body' else 'tag'
    if by_type == 'name':
        return 'name'
    if by_type == 'classname':
        return 'class'
    if by_type == 'xpath':
        return 'xpath_absoluto' if value.strip().startswith('/html') else 'xpath_relativo'
    if by_type == 'css':
        if value.startswith('#') or '[id=' in value:
            return 'id'
        if 'nth-child' in value or ('>' in value and
                any(t in value for t in ['div', 'label', 'span'])):
            return 'css_estrutural'
        if '[class' in value or '*[class' in value or value.startswith('.'):
            return 'class'
        return 'css_outro'
    return 'outros'


FRAGILE = {'xpath_absoluto', 'xpath_relativo', 'css_estrutural', 'class', 'tag_body', 'css_outro'}


def extract_cypress_locators(tree, code):
    counts = {}
    for call in find_nodes(tree.root_node, 'call_expression'):
        if get_call_object(call, code) == 'cy' and get_function_name(call, code) == 'get':
            selector = get_first_argument_text(call, code)
            if selector:
                cat = classify_cypress_selector(selector)
                counts[cat] = counts.get(cat, 0) + 1
    return counts


def extract_selenium_locators(tree, code):
    counts = {}
    for call in find_nodes(tree.root_node, 'call_expression'):
        if get_call_object(call, code) == 'By':
            value = get_first_argument_text(call, code)
            cat = classify_selenium_locator(get_function_name(call, code), value)
            counts[cat] = counts.get(cat, 0) + 1
    return counts


# ─────────────────────────────────────────────────────────────
# TEST SMELLS — hard_coded only (AST-based)
# Other smells (fixed_wait, unsafe_chain, etc.) are detected
# by ESLint (see scripts/eslint-config/).
# ─────────────────────────────────────────────────────────────

def detect_hard_coded_values(tests, code, framework):
    """
    Detects hard-coded problematic values in test bodies:
    - localhost URLs with port numbers
    - Literal email addresses
    - Phone numbers in xxx.xxx.xxxx format
    - Long digit-containing strings inside type()/sendKeys()
      (heuristic for passwords — manual verification recommended)
    """
    import re
    affected = []

    patterns = [
        r'localhost:\d+',
        r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}',
        r'\b\d{3}[\.\-]\d{3}[\.\-]\d{4}\b',
    ]
    password_pattern = re.compile(r"""(?:type|sendKeys)\s*\(\s*['"]([^'"]{6,})['"]""")

    for t in tests:
        body_text = code[t['body_node'].start_byte:t['body_node'].end_byte].decode('utf-8', errors='replace')
        found = any(re.search(pat, body_text, re.IGNORECASE) for pat in patterns)

        if not found:
            for m in password_pattern.findall(body_text):
                if not m.startswith(('#', '.', '[', '/', '@')):
                    if re.search(r'\d', m) and len(m) >= 6:
                        found = True
                        break

        if found:
            affected.append(t['name'])

    return affected


# ─────────────────────────────────────────────────────────────
# MAIN ANALYSIS
# ─────────────────────────────────────────────────────────────

def analyze(file_path, framework, label):
    p = Path(file_path)
    if not p.exists():
        print(f"\n[WARNING] File not found: {file_path}")
        return

    tree, code = parse_file(file_path)

    print(f"\n{'='*60}")
    print(f"  ANALYSIS — {label.upper()}")
    print(f"{'='*60}")

    tests = extract_tests(tree, code)
    n = len(tests)

    # ── GROUP 1 — CONFORMANCE ─────────────────────────────────
    print(f"\n GROUP 1 — CONFORMANCE")
    print(f"  test_case_count        : {n}")

    with_assert = sum(1 for t in tests if count_assertions(t['body_node'], code, framework) > 0)
    ac = round(with_assert / n * 100, 1) if n > 0 else 0
    print(f"  assertion_conformity   : {ac}%  ({with_assert}/{n})")

    with_inter = sum(1 for t in tests if count_interactions(t['body_node'], code, framework) >= 4)
    ic = round(with_inter / n * 100, 1) if n > 0 else 0
    print(f"  interaction_conformity : {ic}%  ({with_inter}/{n})")

    # ── GROUP 2 — COMPLEXITY ──────────────────────────────────
    print(f"\n GROUP 2 — COMPLEXITY")

    total_a = sum(count_assertions(t['body_node'], code, framework) for t in tests)
    avg_a = round(total_a / n, 2) if n > 0 else 0
    print(f"  avg_assertions         : {avg_a}")

    # ── LOCATOR FRAGILITY ─────────────────────────────────────
    print(f"\n LOCATOR FRAGILITY")
    counts = extract_cypress_locators(tree, code) if framework == 'cypress' else extract_selenium_locators(tree, code)

    total_loc = sum(counts.values())
    print(f"  total_locators         : {total_loc}")

    for cat, qty in sorted(counts.items(), key=lambda x: -x[1]):
        pct  = round(qty / total_loc * 100, 1) if total_loc > 0 else 0
        flag = " ← fragile" if cat in FRAGILE else ""
        print(f"    {cat:<25} {qty:>3}  ({pct}%){flag}")

    fragile_count = sum(qty for cat, qty in counts.items() if cat in FRAGILE)
    flr = round(fragile_count / total_loc, 4) if total_loc > 0 else 0

    loc_class    = counts.get('class', 0)
    css_outro    = counts.get('css_outro', 0)
    xpath_rel    = counts.get('xpath_relativo', 0)

    print(f"  fragile_locator_rate   : {flr}  ({round(flr*100,1)}%)")
    print(f"  loc_class              : {loc_class}")
    print(f"  css_outro              : {css_outro}")
    print(f"  xpath_relativo         : {xpath_rel}")

    # ── HARD-CODED SMELL (AST) ────────────────────────────────
    print(f"\n TEST SMELLS (AST)")
    hv = detect_hard_coded_values(tests, code, framework)
    print(f"  smell_hard_coded       : {len(hv)}")
    for name in hv:
        print(f"    → {name}")

    print(f"\n[ESLint smells — run eslint-config separately]")
    print(f"  eslint_cy_wait_fixo, eslint_unsafe_chain, eslint_await_loop,")
    print(f"  eslint_no_only_test, eslint_no_unused_var,")
    print(f"  max_lines_per_function, max_statements")


# ─────────────────────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    analyze(CYPRESS_FILE,  "cypress",  "Cypress")
    analyze(SELENIUM_FILE, "selenium", "Selenium")