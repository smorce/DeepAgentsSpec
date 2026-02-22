"""Auto-generated mutation module for agent radar."""

MUTATION_ID = "EXP-019"
MUTATION_TITLE = "[qwen] Global-batch load balance almost free lunch to improve your MoE LLM training"
MUTATION_SOURCE = "qwen"
THEMES = ["mcp", "skills", "observability"]

def mutate(new_item):
    item = dict(new_item)
    tags = item.get('harness_tags', [])
    if not isinstance(tags, list):
        tags = []
    for theme in THEMES:
        if theme not in tags:
            tags.append(theme)
    item['harness_tags'] = tags
    item['state_checkpoint_policy'] = ["before_external_io", "before_long_running_loop", "before_quality_gate"]
    item['conversation_replacements'] = ["[[STATE_REF:<id>]]", "[[PLAN_REF:<epic>/<feature>]]", "[[EVAL_REF:<run>]]"]
    high_priority_themes = set(["control", "evals", "feedback", "observability", "reliability", "safety"])
    medium_priority_themes = set(["context", "environment", "maintainability", "mcp", "scalability", "skills"])
    theme_set = {str(theme).strip().lower() for theme in THEMES}
    if theme_set.intersection(high_priority_themes):
        item['innovation_priority'] = 'high'
    elif theme_set.intersection(medium_priority_themes):
        item['innovation_priority'] = 'medium'
    else:
        item['innovation_priority'] = 'normal'
    item['mutation_module'] = "mutation_exp_019"
    return item
