"""Auto-generated mutation module for agent radar."""

MUTATION_ID = "EXP-001"
MUTATION_TITLE = "MCP/Skills関連の新規記事を検出したときに自動で評価タスクへ変換する"
MUTATION_SOURCE = "system"
THEMES = ["mcp", "skills"]

def mutate(new_item):
    item = dict(new_item)
    tags = item.get('harness_tags', [])
    if not isinstance(tags, list):
        tags = []
    for theme in THEMES:
        if theme not in tags:
            tags.append(theme)
    item['harness_tags'] = tags
    item['state_checkpoint_policy'] = [
        'before_external_io',
        'before_long_running_loop',
        'before_quality_gate',
    ]
    item['conversation_replacements'] = [
        '[[STATE_REF:<id>]]',
        '[[PLAN_REF:<epic>/<feature>]]',
        '[[EVAL_REF:<run>]]',
    ]
    if 'mcp' in THEMES or 'skills' in THEMES:
        item['innovation_priority'] = 'high'
    elif 'observability' in THEMES or 'context' in THEMES:
        item['innovation_priority'] = 'medium'
    else:
        item['innovation_priority'] = 'normal'
    item['mutation_module'] = "mutation_exp_001"
    return item
