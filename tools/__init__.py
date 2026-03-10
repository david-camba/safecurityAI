from .human_task import human_task
from .log_improvement import log_improvement
from .hashlookup_api import check_hash_circl
from .finish_analysis import finish_analysis

# Esta es la lista mágica que le enchufaremos al LLM Supporter
AVAILABLE_TOOLS = [human_task, log_improvement, check_hash_circl]